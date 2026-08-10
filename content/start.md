---
title: "Getting Started"
linkTitle: "Quick Start"
description: "Get PG Exporter running and expose PostgreSQL metrics to Prometheus in five minutes"
weight: 20
icon: fa-solid fa-rocket
categories: [Reference]
---

This page is the shortest path: install **PG Exporter**, connect it to a PostgreSQL instance, verify metrics output, and hook it into Prometheus.

You only need two things: a reachable PostgreSQL 10-19+ (or PgBouncer 1.8+) instance, and permission to create a user in it. For older PostgreSQL 9.1-9.6 instances, see [Compatibility](/compatibility/).

{{% steps %}}

## Install {#install}

On Linux amd64 you can download the binary directly. For managed packages, other platforms, containers, Pigsty, and source builds, use the [download guide](/download/).

```bash
VERSION=$(curl -fsSL https://api.github.com/repos/pgsty/pg_exporter/releases/latest | sed -n 's/.*"tag_name": "v\([^"]*\)".*/\1/p')
wget "https://github.com/pgsty/pg_exporter/releases/download/v${VERSION}/pg_exporter-${VERSION}.linux-amd64.tar.gz"
mkdir -p "pg_exporter-${VERSION}.linux-amd64"
tar -xf "pg_exporter-${VERSION}.linux-amd64.tar.gz" -C "pg_exporter-${VERSION}.linux-amd64"
sudo install "pg_exporter-${VERSION}.linux-amd64/pg_exporter" /usr/bin/
sudo install "pg_exporter-${VERSION}.linux-amd64/pg_exporter.yml" /etc/pg_exporter.yml
```

Confirm the installation:

```bash
pg_exporter --version
# pg_exporter v{{< param version >}} (built with go1.26.5 on linux/amd64)
```

## Create a Monitoring User {#create-monitoring-user}

Create a dedicated monitoring user on the target PostgreSQL. The built-in `pg_monitor` role (PostgreSQL 10+) covers all read permissions the default collectors need:

```sql
CREATE USER monitor WITH PASSWORD 'S3cret';
GRANT pg_monitor TO monitor;
```

If you are just trying it out locally as a superuser such as `postgres`, you can skip this step.

## Run and Verify {#run-and-verify}

Use `--dry-run` to confirm the configuration parses, then start for real:

```bash
export PG_EXPORTER_URL='postgres://monitor:S3cret@localhost:5432/postgres'

pg_exporter --dry-run     # print parsed collector config, then exit
pg_exporter               # start for real, listening on :9630 by default
```

Without any URL, `pg_exporter` falls back to the local-first default `postgresql:///?sslmode=disable`, which fits running on the same host as PostgreSQL. The full URL source precedence (`--url` > `PG_EXPORTER_URL` > `PGURL` > `PG_EXPORTER_URL_FILE` > default) is documented in the [Deployment guide](/deploy/).

Pull the metrics from another terminal:

```bash
curl -s http://localhost:9630/metrics | grep -E '^pg_(up|version|in_recovery) '
```

You should see the three core built-in metrics:

```prometheus
pg_up 1              # 1 when the target is reachable, 0 otherwise
pg_version 170000    # version in server_version_num format
pg_in_recovery 0     # 1 on replicas, 0 on primaries
```

`pg_up 1` means the pipeline works — the remaining 600+ metrics (`pg_db_*`, `pg_table_*`, `pg_wal_*`, ...) all come from the declarative collector definitions in `pg_exporter.yml`. If `pg_up` is `0`, restart with `pg_exporter --log.level=debug` and inspect the connection error.

## Hook into Prometheus {#hook-into-prometheus}

Add a scrape target in `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'postgresql'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:9630']
```

Collectors cache results per their `ttl` (most realtime collectors use `ttl: 10`): as long as the TTL is below the scrape interval, every scrape gets fresh data, while high-frequency scraping can never overwhelm the database. This is also why setting `scrape_interval` below the common TTLs is not recommended.

That's it. For Grafana, you can reuse the PostgreSQL dashboards from [Pigsty](https://pigsty.io), or explore the [live demo](https://g.pgsty.com).

{{% /steps %}}

## Troubleshooting

| Symptom                     | What to do                                                                                                 |
|-----------------------------|------------------------------------------------------------------------------------------------------------|
| `pg_up 0`, connection fails | Run `pg_exporter --log.level=debug` and read the error; check URL, `pg_hba.conf`, and network reachability |
| Some metrics are missing    | `curl localhost:9630/explain` to see each collector's planning verdict (version gates, tags, predicates)   |
| A collector keeps failing   | `curl localhost:9630/stat` for per-collector error counters and durations                                  |
| Scrapes are slow            | Find the slow collector in `/stat`, raise its `ttl`, or set `skip: true`                                   |
{.full-width}

`/stat`, `/explain`, and `/reload` are management endpoints — protect them with `--web.config.file` (TLS/auth) or keep them on a trusted network in production. See the [API Reference](/api/).

## Next Steps

- Monitor **PgBouncer**, enable **auto-discovery**, deploy with **systemd / Docker / Kubernetes**: [Deployment guide](/deploy/)
- Understand and customize **collectors** (GAUGE/COUNTER/HISTOGRAM, TTL, tags, version gates): [Configuration reference](/config/)
- **Health check and primary/replica traffic routing** endpoints (`/up`, `/primary`, `/replica`): [API Reference](/api/)
