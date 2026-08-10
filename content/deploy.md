---
title: "Production Deployment"
linkTitle: "Deployment"
description: "Run pg_exporter with systemd, Docker, or Kubernetes and connect it to Prometheus"
weight: 50
icon: fa-solid fa-boxes-packing
categories: [Reference]
---

This page covers what it takes to run `pg_exporter` in production: process arguments and environment variables, monitoring user and credential management, the systemd / Docker / Kubernetes deployment forms, PgBouncer and auto-discovery, plus scrape and alerting configuration on the Prometheus side.

Process-level configuration comes from two sources, in decreasing precedence:

1. **Command-line arguments** (`--url`, `--config`, ...)
2. **Environment variables** (every flag has a corresponding `PG_EXPORTER_*` variable)

Metric collection behavior is entirely driven by YAML collector definitions (default `/etc/pg_exporter.yml`, or a config directory) — see the [Configuration reference](/config/).

--------

## Command-Line Arguments

```bash
pg_exporter \
  --url="postgres://monitor:S3cret@localhost:5432/postgres" \
  --config="/etc/pg_exporter.yml" \
  --web.listen-address=":9630" \
  --auto-discovery \
  --log.level="info"
```

The full flag list from `pg_exporter --help`:

```bash
Flags:
  -h, --[no-]help                Show context-sensitive help (also try --help-long and --help-man).
  -u, --url=URL                  postgres target url
  -c, --config=CONFIG            path to config dir or file
      --web.listen-address=:9630 ...
                                 Addresses on which to expose metrics and web interface. Repeatable for multiple addresses. Examples: `:9100` or `[::1]:9100` for http, `vsock://:9100` for vsock
      --web.config.file=""       Path to configuration file that can enable TLS or authentication. See: https://github.com/prometheus/exporter-toolkit/blob/master/docs/web-configuration.md
  -l, --label=""                 constant labels: comma separated list of label=value pair ($PG_EXPORTER_LABEL)
  -t, --tag=""                   tags, comma separated list of server tag ($PG_EXPORTER_TAG)
  -C, --[no-]disable-cache       force not using cache ($PG_EXPORTER_DISABLE_CACHE)
  -m, --[no-]disable-intro       disable internal/exporter self-monitoring metrics (only expose query metrics) ($PG_EXPORTER_DISABLE_INTRO)
  -a, --[no-]auto-discovery      automatically scrape all databases on the target server ($PG_EXPORTER_AUTO_DISCOVERY)
  -x, --exclude-database="template0,template1,postgres"
                                 excluded databases when auto-discovery is enabled ($PG_EXPORTER_EXCLUDE_DATABASE)
  -i, --include-database=""      included databases when auto-discovery is enabled ($PG_EXPORTER_INCLUDE_DATABASE)
  -n, --namespace=""             prefix of built-in metrics, (pg|pgbouncer) by default ($PG_EXPORTER_NAMESPACE)
  -f, --[no-]fail-fast           fail fast instead of waiting during start-up ($PG_EXPORTER_FAIL_FAST)
  -T, --connect-timeout=100      connect timeout in ms, 100 by default ($PG_EXPORTER_CONNECT_TIMEOUT)
  -P, --web.telemetry-path="/metrics"
                                 URL path under which to expose metrics ($PG_EXPORTER_TELEMETRY_PATH)
  -D, --[no-]dry-run             dry run and print raw configs
  -E, --[no-]explain             explain server planned queries
      --log.level="info"         log level: debug|info|warn|error
      --log.format="logfmt"      log format: logfmt|json
      --[no-]version             Show application version.
```

Two deployment-relevant behaviors worth knowing:

- **Startup policy**: non-blocking startup is the default — when the target database is temporarily unreachable, the HTTP endpoints come up anyway and a background probe keeps retrying until recovery. If you prefer "fail on unreachable" (e.g. delegating restart decisions to systemd or an orchestrator), set `--fail-fast`.
- **Telemetry path validation**: since v1.4.0, `--web.telemetry-path` is strictly validated at startup — empty paths, conflicts with built-in endpoints, or non-canonical paths like `//metrics` that could never match fail immediately with a clear error.

### Connection URL Sources

The connection string resolves from the following sources, first non-empty value wins:

1. `--url` / `-u` command-line argument
2. `PG_EXPORTER_URL` environment variable
3. `PGURL` environment variable
4. Content of the file pointed to by `PG_EXPORTER_URL_FILE` (fits container Secret mounts)
5. Default `postgresql:///?sslmode=disable` (local-first, fits same-host deployment)

When the URL omits `sslmode`, `sslmode=disable` is appended automatically. Also, libpq service-file environment variables (`PGSERVICE` / `PGSERVICEFILE`, etc.) are cleared at startup with a log line — service files could override the explicit connection target, and `pg_exporter` guarantees that the URL announced in logs is the URL actually connected to.

--------

## Monitoring User and Credentials

### Create the Monitoring User

```sql
CREATE ROLE monitor WITH LOGIN PASSWORD 'S3cret' CONNECTION LIMIT 5;
GRANT pg_monitor TO monitor;   -- built-in monitoring role (PostgreSQL 10+), covers all default collectors
```

Keeping `CONNECTION LIMIT` is recommended: the exporter normally holds only one to a few connections (one per database with auto-discovery), and the limit prevents connection exhaustion on misconfiguration.

### Manage Passwords with .pgpass

Take the password out of the URL and let libpq's `.pgpass` provide it:

```bash
# Create as the OS user that runs the exporter
echo "localhost:5432:*:monitor:S3cret" > ~/.pgpass
chmod 600 ~/.pgpass

# URL without password
PG_EXPORTER_URL='postgres://monitor@localhost:5432/postgres'
```

{{% alert title="RPM/DEB package installs" color="info" %}}
Packaged services run as the `prometheus` system user. Since v1.4.0 its HOME points to `/var/lib/prometheus` (where libpq looks up `~/.pgpass`), but the package does **not** create that directory. Before using `.pgpass`, run:
`install -d -o prometheus -g prometheus /var/lib/prometheus`
{{% /alert %}}

### TLS for the Database Connection

```bash
PG_EXPORTER_URL='postgres://monitor:S3cret@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pki/ca.crt'
```

### Protecting the HTTP Port

Beyond `/metrics`, the `/reload`, `/explain`, and `/stat` management endpoints let anyone with port access read configuration and runtime state, or trigger reloads. If the exporter is reachable from a shared network, enable TLS / Basic Auth via `--web.config.file` ([exporter-toolkit web configuration](https://github.com/prometheus/exporter-toolkit/blob/master/docs/web-configuration.md)), or restrict access at the firewall / reverse-proxy layer.

--------

## Systemd Deployment (RPM/DEB packages)

The RPM/DEB packages ship a service unit and an environment file; after installation, edit the environment file and start:

```ini
# /usr/lib/systemd/system/pg_exporter.service
[Unit]
Description=Prometheus exporter for PostgreSQL/Pgbouncer server metrics
Documentation=https://pigsty.io/docs
After=network.target

[Service]
EnvironmentFile=-/etc/default/pg_exporter
User=prometheus
ExecStart=/usr/bin/pg_exporter $PG_EXPORTER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Environment file `/etc/default/pg_exporter` (package defaults):

```bash
PG_EXPORTER_URL='postgres://:5432/postgres?sslmode=disable'
PG_EXPORTER_CONFIG=/etc/pg_exporter.yml
PG_EXPORTER_LABEL=""
PG_EXPORTER_TAG=""
PG_EXPORTER_DISABLE_CACHE=false
PG_EXPORTER_AUTO_DISCOVERY=true
PG_EXPORTER_EXCLUDE_DATABASE="template0,template1,postgres"
PG_EXPORTER_INCLUDE_DATABASE=""
PG_EXPORTER_NAMESPACE="pg"
PG_EXPORTER_FAIL_FAST=false
PG_EXPORTER_CONNECT_TIMEOUT=100
PG_EXPORTER_TELEMETRY_PATH="/metrics"
PG_EXPORTER_OPTS='--log.level=info'
```

Every command-line flag has a corresponding environment variable — append what you need here (e.g. `PG_EXPORTER_DISABLE_INTRO`). The file is packaged as `noreplace`, so upgrades never overwrite your edits.

Common operations:

```bash
sudo systemctl enable --now pg_exporter    # start and enable at boot
sudo systemctl status pg_exporter          # check status
journalctl -u pg_exporter -f               # follow logs
curl -X POST localhost:9630/reload         # hot-reload collector config (no restart)
```

--------

## Docker Deployment

```bash
docker run -d \
  --name pg_exporter \
  --restart unless-stopped \
  -p 9630:9630 \
  -e PG_EXPORTER_URL="postgres://monitor:S3cret@host:5432/postgres" \
  pgsty/pg_exporter:latest
```

Docker Compose:

```yaml
services:
  pg_exporter:
    image: pgsty/pg_exporter:latest
    container_name: pg_exporter
    restart: unless-stopped
    ports:
      - "9630:9630"
    environment:
      - PG_EXPORTER_URL=postgres://monitor:S3cret@postgres:5432/postgres
    volumes:
      - ./pg_exporter.yml:/etc/pg_exporter.yml:ro   # optional: custom collector config
    depends_on:
      - postgres
```

{{% alert title="Note" color="warning" %}}
The official image is built from `scratch` and contains no system CA certificates. When connecting to remote PostgreSQL with `sslmode=verify-ca` / `verify-full`, mount a CA certificate explicitly and point `sslrootcert` at it, or TLS verification cannot complete.
{{% /alert %}}

--------

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pg-exporter
  labels: { app: pg-exporter }
spec:
  replicas: 1
  selector:
    matchLabels: { app: pg-exporter }
  template:
    metadata:
      labels: { app: pg-exporter }
    spec:
      containers:
      - name: pg-exporter
        image: pgsty/pg_exporter:latest
        ports:
        - containerPort: 9630
        env:
        - name: PG_EXPORTER_URL
          valueFrom:
            secretKeyRef:
              name: pg-credentials
              key: connection-url
        livenessProbe:
          httpGet: { path: /liveness, port: 9630 }
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet: { path: /readiness, port: 9630 }
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests: { cpu: 100m, memory: 128Mi }
          limits: { cpu: 200m, memory: 256Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: pg-exporter
  labels: { app: pg-exporter }
spec:
  ports:
  - { port: 9630, targetPort: 9630, name: metrics }
  selector: { app: pg-exporter }
```

You can also use `PG_EXPORTER_URL_FILE` pointing at a Secret-mounted file, keeping the connection string out of environment variables.

--------

## Auto-Discovery

Auto-discovery (enabled by default) lets one exporter instance monitor every database in the target PostgreSQL:

```bash
pg_exporter --auto-discovery \
  --exclude-database="template0,template1,postgres" \  # default exclusion list
  --include-database=""                                # set to switch to allowlist mode
```

Behavior:

- Cluster-level collectors (`tags: [cluster]`) run once on the primary connection
- Database-level collectors run on every discovered database, with metrics distinguished by the `datname` label
- Newly created / dropped databases are picked up / removed in subsequent planning cycles

--------

## Monitoring PgBouncer

Set the database name in the URL to `pgbouncer` to switch to PgBouncer mode (this is what triggers the detection):

```bash
PG_EXPORTER_URL='postgres://stats_user:S3cret@localhost:6432/pgbouncer' pg_exporter
```

In PgBouncer mode, the exporter uses the `pgbouncer` metric prefix and runs only PgBouncer-specific collectors (`SHOW STATS` / `SHOW POOLS`, etc.). The usual pattern is one exporter instance for PostgreSQL and another for PgBouncer, on different ports.

--------

## Prometheus Scraping and Alerting

### Scrape Configuration

```yaml
scrape_configs:
  - job_name: 'postgresql'
    scrape_interval: 15s
    static_configs:
      - targets: ['pg-1:9630', 'pg-2:9630', 'pg-3:9630']
```

Kubernetes service discovery:

```yaml
scrape_configs:
  - job_name: 'postgresql'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: pg-exporter
        action: keep
      - source_labels: [__meta_kubernetes_pod_ip]
        target_label: __address__
        replacement: ${1}:9630
```

Keep the scrape interval at or above the common collector `ttl` (mostly 10 seconds in the default bundle): TTL caching means more frequent scrapes would only receive cached results anyway.

### Alert Rules

All rules below are based on metrics that actually exist:

```yaml
groups:
  - name: pg_exporter
    rules:
      # Exporter process unreachable
      - alert: PgExporterDown
        expr: up{job="postgresql"} == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "pg_exporter down ({{ $labels.instance }})"

      # Exporter alive but cannot reach the database
      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "PostgreSQL connection failed ({{ $labels.instance }})"

      # Overall scrape duration abnormal (unit: seconds)
      - alert: PgExporterSlowScrape
        expr: pg_exporter_scrape_duration > 10
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "pg_exporter slow scrape ({{ $labels.instance }})"

      # A specific collector keeps failing (locate by datname/query)
      - alert: PgExporterQueryError
        expr: increase(pg_exporter_query_scrape_error_count[10m]) > 0
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "Collector {{ $labels.query }} keeps failing on {{ $labels.datname }}"
```

### Role-Based Traffic Routing

The `/primary`, `/replica`, and `/read` health-check endpoints can serve directly as health probes for HAProxy and similar load balancers, enabling primary/replica read-write splitting. Endpoint semantics and a complete HAProxy example are in the [API Reference](/api/#traffic-routing).

Note: open-source Nginx does not support active out-of-band HTTP health checks (`health_check` is an NGINX Plus feature). For role-based PostgreSQL traffic routing, prefer HAProxy, or solutions like Patroni + vip-manager.
