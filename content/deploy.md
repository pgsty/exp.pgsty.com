---
title: "Production Deployment"
linkTitle: "Deployment"
description: "Run pg_exporter with systemd, Docker, or Kubernetes and connect it to Prometheus"
weight: 50
icon: fa-solid fa-boxes-packing
categories: [Reference]
---

Install the [release package](/install/), create a monitoring role, then choose systemd, Docker, or Kubernetes below. Finish by checking `/metrics` and adding the exporter to Prometheus.

The [Command Reference](/cmd/) lists flags, environment variables, defaults, and precedence. Command-line settings take priority over their environment aliases. Logging, action, and exporter-toolkit web flags use the command line only. Collector SQL and metric definitions belong in [YAML configuration](/config/).

## Process Settings

This foreground example uses `.pgpass` for the database password:

```bash
pg_exporter \
  --url='postgres://monitor@localhost:5432/postgres' \
  --config=/etc/pg_exporter.yml \
  --web.listen-address=:9630 \
  --log.level=info
```

Auto-discovery is enabled by default. If the database is unavailable at startup, the exporter starts its HTTP listener and retries in the background. Set `--fail-fast` to exit when the initial database check fails.

### Connection URL Sources

Set the target with `--url` or `PG_EXPORTER_URL`, or read a secret file through `PG_EXPORTER_URL_FILE`. See the command reference for the complete [precedence rules](/cmd/#target-and-configuration-precedence). A URL without `sslmode` uses `disable`; set it explicitly for remote TLS connections.

To use a URL file, clear `PG_EXPORTER_URL` and `PGURL`, and omit `--url`. For a packaged service, also remove the default `PG_EXPORTER_URL` line from `/etc/default/pg_exporter`.

## Monitoring User and Credentials

### Create the Monitoring User

```sql
CREATE ROLE monitor WITH LOGIN PASSWORD 'replace-this-secret' CONNECTION LIMIT 5;
GRANT pg_monitor TO monitor;   -- PostgreSQL 10+
```

The main target pool allows up to three connections. Each additional discovered database allows one. Size `CONNECTION LIMIT` for that total and for any other exporters sharing the role. Grant `CONNECT` on each target database if it is not already available; optional views and extensions can need further grants. See [Security](/security/).

### Manage Passwords with .pgpass

Take the password out of the URL and let libpq's `.pgpass` provide it:

```bash
# Create as the OS user that runs the exporter
umask 077
printf '%s\n' 'localhost:5432:*:monitor:replace-this-secret' > ~/.pgpass
chmod 600 ~/.pgpass

# URL without password
export PG_EXPORTER_URL='postgres://monitor@localhost:5432/postgres'
```

The package runs the service as `prometheus`. Check its home with `getent passwd prometheus` and install `.pgpass` there. Newly created package accounts use `/var/lib/prometheus`; [Security](/security/#pgpass) gives the directory and file installation commands.

### TLS for the Database Connection

```bash
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pg_exporter/ca.crt'
```

### Protecting the HTTP Port

Beyond `/metrics`, the `/reload`, `/explain`, and `/stat` management endpoints let anyone with port access read configuration and runtime state, or trigger reloads. If the exporter is reachable from a shared network, enable TLS / Basic Auth via `--web.config.file` ([exporter-toolkit web configuration](https://github.com/prometheus/exporter-toolkit/blob/v0.20.0/docs/web-configuration.md)), or restrict access at the firewall / reverse-proxy layer.

## Systemd Deployment (RPM/DEB packages)

The packages install the binary at `/usr/bin/pg_exporter`, collectors at `/etc/pg_exporter.yml`, and settings at `/etc/default/pg_exporter`. The unit is `/usr/lib/systemd/system/pg_exporter.service` for RPM and `/lib/systemd/system/pg_exporter.service` for DEB:

```ini
# /usr/lib/systemd/system/pg_exporter.service
[Unit]
Description=Prometheus exporter for PostgreSQL/Pgbouncer server metrics
Documentation=https://pigsty.io/docs/pg_exporter
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

Replace the default URL with your monitoring user and target. Add settings with environment aliases, such as `PG_EXPORTER_DISABLE_INTRO`, directly to this file. Put command-line-only flags in `PG_EXPORTER_OPTS`. The package marks the environment and collector files as configuration files to preserve local edits during upgrades.

Start and verify the service:

```bash
sudo systemctl enable --now pg_exporter
sudo systemctl status pg_exporter --no-pager
curl -fsS http://127.0.0.1:9630/metrics
sudo journalctl -u pg_exporter -n 50 --no-pager
```

Check that the metrics include `pg_up 1`. To follow new log entries, run `sudo journalctl -u pg_exporter -f`.

After editing `/etc/default/pg_exporter`, run `sudo systemctl restart pg_exporter`. For changes to collector YAML only, reload it directly:

```bash
curl -fsS -X POST http://127.0.0.1:9630/reload
```

## Docker Deployment

Create `pg_exporter.url` with your database connection URL. This example expects a TLS certificate for `db.example.com` and a CA file named `ca.crt`:

```text
postgres://monitor:replace-this-secret@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/run/secrets/pg-ca.crt
```

Keep the URL file private, then mount it and the CA into the container:

```bash
chmod 600 pg_exporter.url
docker run -d \
  --name pg_exporter \
  --restart unless-stopped \
  -p 9630:9630 \
  -v "$PWD/pg_exporter.url:/run/secrets/pg_exporter_url:ro" \
  -v "$PWD/ca.crt:/run/secrets/pg-ca.crt:ro" \
  -e PG_EXPORTER_URL_FILE=/run/secrets/pg_exporter_url \
  pgsty/pg_exporter:{{< param version >}}
```

Docker Compose:

```yaml
services:
  pg_exporter:
    image: pgsty/pg_exporter:{{< param version >}}
    restart: unless-stopped
    ports:
      - "9630:9630"
    environment:
      PG_EXPORTER_URL_FILE: /run/secrets/pg_exporter_url
    volumes:
      - ./pg_exporter.url:/run/secrets/pg_exporter_url:ro
      - ./ca.crt:/run/secrets/pg-ca.crt:ro
```

The image includes the default collector configuration. To replace it, add a read-only mount at `/etc/pg_exporter.yml`. It is a `scratch` image with no shell or CA bundle, so the CA mount above is required for this TLS example.

Check the running container:

```bash
docker logs pg_exporter
curl -fsS http://127.0.0.1:9630/metrics
```

Publish port 9630 on an address reachable by Prometheus and restrict its network access. If Prometheus runs on the Docker host, use `-p 127.0.0.1:9630:9630`.

## Kubernetes Deployment

Create a Secret from the URL and CA files above, in the namespace where the exporter will run:

```bash
kubectl create secret generic pg-exporter-connection \
  --from-file=connection-url=./pg_exporter.url \
  --from-file=pg-ca.crt=./ca.crt
```

Save this manifest as `pg-exporter.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pg-exporter
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
        image: pgsty/pg_exporter:{{< param version >}}
        ports:
        - { name: metrics, containerPort: 9630 }
        env:
        - name: PG_EXPORTER_URL_FILE
          value: /run/secrets/connection-url
        volumeMounts:
        - name: connection
          mountPath: /run/secrets
          readOnly: true
        livenessProbe:
          httpGet: { path: /version, port: metrics }
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet: { path: /version, port: metrics }
          periodSeconds: 5
        resources:
          requests: { cpu: 100m, memory: 128Mi }
          limits: { cpu: 200m, memory: 256Mi }
      volumes:
      - name: connection
        secret:
          secretName: pg-exporter-connection
---
apiVersion: v1
kind: Service
metadata:
  name: pg-exporter
spec:
  ports:
  - { port: 9630, targetPort: metrics, name: metrics }
  selector: { app: pg-exporter }
```

Both probes use `/version` to check that the exporter can serve HTTP. `/liveness` and `/readiness` are aliases of `/up`: they report database health. Using them here would restart the exporter or remove its Service endpoint during a database outage, when its metrics are most useful.

Apply the manifest and check the rollout:

```bash
kubectl apply -f pg-exporter.yaml
kubectl rollout status deployment/pg-exporter
kubectl logs deployment/pg-exporter
kubectl port-forward service/pg-exporter 9630:9630
```

While port forwarding runs, check `/metrics` from another terminal. Adjust the resource requests and limits after measuring your collector workload. If HTTP authentication is enabled, configure the probes to authenticate as well.

## Auto-Discovery

Auto-discovery adds eligible databases from the same PostgreSQL instance. Use an include list to limit it to selected databases:

```bash
pg_exporter --auto-discovery \
  --exclude-database="template0,template1,postgres" \
  --include-database="app,analytics"
```

The URL database is always monitored. Include/exclude lists apply only to additional databases; exclusion wins if a name appears in both lists. An empty include list allows all otherwise eligible databases.

- Cluster-level collectors (`tags: [cluster]`) run once on the main connection.
- Database-level collectors also run on discovered databases. Bundled collectors use `datname` labels to identify results; custom SQL must supply its declared labels.
- Each scrape checks for created or dropped databases.
- `--no-auto-discovery` restricts collection to the URL database.

## Monitoring PgBouncer

Set the database name in the URL to `pgbouncer` to switch to PgBouncer mode (this is what triggers the detection):

```bash
PG_EXPORTER_URL='postgres://stats_user@localhost:6432/pgbouncer' \
pg_exporter --namespace=pgbouncer --web.listen-address=:9631
```

Supply this account through PgBouncer authentication and add it to `stats_users`. Store its password in `.pgpass`. In this mode, the exporter runs the PgBouncer `SHOW` collectors. Run separate exporter processes for PostgreSQL and PgBouncer, with separate ports.

The default self-metric namespace is `pgbouncer` when no namespace is set. The package environment file sets `PG_EXPORTER_NAMESPACE=pg`; change it to `pgbouncer` for a packaged PgBouncer service. This setting affects built-in self-metrics, not YAML-defined metric names.

## Prometheus Scraping and Alerting

### Scrape Configuration

```yaml
scrape_configs:
  - job_name: 'postgresql'
    scrape_interval: 15s
    scrape_timeout: 10s
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
      - source_labels: [__meta_kubernetes_pod_container_port_name]
        regex: metrics
        action: keep
```

Start with a 15-second interval and a 10-second scrape timeout. A collector result can be reused until its `ttl` expires; many bundled collectors use 10 seconds. Measure total scrape duration before reducing the interval or increasing the number of databases.

### Alert Rules

These examples use the default `pg` self-metric namespace:

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

      # Main target connection or a fatal collector failed
      - alert: PostgreSQLDown
        expr: pg_up{job="postgresql"} == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "PostgreSQL scrape failed ({{ $labels.instance }})"

      # Overall scrape duration abnormal (unit: seconds)
      - alert: PgExporterSlowScrape
        expr: pg_exporter_scrape_duration{job="postgresql"} > 8
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "pg_exporter slow scrape ({{ $labels.instance }})"
```

### Role-Based Traffic Routing

The `/primary`, `/replica`, and `/read` health-check endpoints can serve directly as health probes for HAProxy and similar load balancers, enabling primary/replica read-write splitting. Endpoint semantics and a complete HAProxy example are in the [API Reference](/api/#traffic-routing).
