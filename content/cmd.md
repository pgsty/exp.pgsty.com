---
title: "Command Reference"
linkTitle: "Command Reference"
description: "PG Exporter command-line flags, environment variables, defaults, and precedence"
weight: 105
icon: fa-solid fa-terminal
categories: [Reference]
---

This page lists flags and environment variables for stable PG Exporter
**v{{< param version >}}**. Use it to choose process flags and environment variables;
use [Collector Configuration](/config/) for the YAML and SQL metric schema.

```bash
pg_exporter [flags]
pg_exporter --help       # concise help
pg_exporter --help-long  # expanded help
pg_exporter --help-man   # man-page form
```

Boolean options use `--flag` to enable and `--no-flag` to disable. The equivalent
`--flag=true` and `--flag=false` forms are normalized before parsing.

## Target and Configuration Precedence

PG Exporter selects the connection URL in this order:

1. `--url` or `-u`
2. `PG_EXPORTER_URL`
3. `PGURL`
4. the trimmed contents of the file named by `PG_EXPORTER_URL_FILE`
5. `postgresql:///?sslmode=disable`

A higher-priority URL takes precedence over the URL file. If the file is selected, it must be readable and contain a nonempty valid URL. Malformed URL syntax, escaping, or query parameter names stop startup without logging the connection string.

Explicit database identity follows `lib/pq`, including `dbname` and `database` query aliases. Auto-discovery replaces the path and removes both aliases before connecting to each discovered database, preserving credentials, TLS options, and special characters in the database name.

If the URL does not specify `sslmode`, PG Exporter adds `sslmode=disable`. The
collector configuration is resolved independently: `--config`, then
`PG_EXPORTER_CONFIG`, then the first existing path among `pg_exporter.yml`,
`/etc/pg_exporter.yml`, and `/etc/pg_exporter`. An explicitly selected path must load successfully; PG Exporter does not fall back to another path on failure.

The driver accepts connection defaults such as `PGHOST`, `PGPORT`, `PGUSER`,
`PGDATABASE`, and `PGPASSFILE` for fields omitted from the URL. PG Exporter clears
`PGSERVICE` and `PGSERVICEFILE`, so service-file settings do not override the target.
Use [Deployment](/deploy/) for credential-file setup.

## Collection Flags

| Flag | Environment | Default | Purpose |
|:---|:---|:---|:---|
| `-u`, `--url=URL` | special precedence above | local libpq URL | PostgreSQL or PgBouncer target |
| `-c`, `--config=PATH` | `PG_EXPORTER_CONFIG` | first existing standard path | Collector YAML file or directory |
| `-l`, `--label=KEY=VALUE,...` | `PG_EXPORTER_LABEL` | empty | Constant Prometheus labels |
| `-t`, `--tag=TAG,...` | `PG_EXPORTER_TAG` | empty | Server tags used by collector planning |
| `-C`, `--[no-]disable-cache` | `PG_EXPORTER_DISABLE_CACHE` | `false` | Bypass main-query result caches |
| `-m`, `--[no-]disable-intro` | `PG_EXPORTER_DISABLE_INTRO` | `false` | Hide built-in target and exporter metrics |
| `-a`, `--[no-]auto-discovery` | `PG_EXPORTER_AUTO_DISCOVERY` | `true` | Discover and scrape databases on the target server |
| `-x`, `--exclude-database=LIST` | `PG_EXPORTER_EXCLUDE_DATABASE` | `template0,template1,postgres` | Exclude databases during auto-discovery |
| `-i`, `--include-database=LIST` | `PG_EXPORTER_INCLUDE_DATABASE` | empty | Restrict auto-discovery to named databases |
| `-n`, `--namespace=NAME` | `PG_EXPORTER_NAMESPACE` | automatic | Override the built-in `pg` or `pgbouncer` metric prefix |
| `-f`, `--[no-]fail-fast` | `PG_EXPORTER_FAIL_FAST` | `false` | Exit when the initial target probe fails |
| `-T`, `--connect-timeout=MS` | `PG_EXPORTER_CONNECT_TIMEOUT` | `100` | Target precheck and health-probe timeout in milliseconds |
{.wide .expand}

`--include-database` and `--exclude-database` apply only when auto-discovery is
enabled. They filter additional connections; the database in `--url` is always
scraped. Exclusions take precedence over inclusions.

`--namespace` changes built-in metric names, such as `pg_up`; it does not rename
YAML metrics. `--disable-intro` also hides `pg_up`, `pg_version`, and
`pg_in_recovery`, but leaves Go/process metrics and health endpoints available.
`--disable-cache` bypasses the main result cache; each predicate keeps its own
configured cache.

Set `--connect-timeout` above the target’s normal round-trip time. A value of zero
or less uses 100 ms. Collector SQL uses its separate YAML `timeout`.
Constant labels appear on exported series. Tags select eligible collectors.

## HTTP Flags

| Flag | Environment | Default | Purpose |
|:---|:---|:---|:---|
| `--web.listen-address=ADDR` | — | `:9630` | Listen address; repeat the flag for multiple addresses |
| `--[no-]web.systemd-socket` | — | `false` | Use systemd socket activation on Linux |
| `--web.config.file=PATH` | — | empty | exporter-toolkit TLS and authentication configuration |
| `-P`, `--web.telemetry-path=PATH` | `PG_EXPORTER_TELEMETRY_PATH` | `/metrics` | Prometheus exposition path |
{.wide .expand}

The telemetry path must start with `/`. It cannot contain a query, fragment,
wildcard, repeated slash, or `..` path segment. It must not collide with built-in routes
such as `/up`, `/primary`, `/replica`, `/reload`, `/explain`, `/stat`, or
`/version`. Startup also verifies that a request for this path actually reaches the metrics handler, rather than a redirect or another handler. Escaped paths must be valid for the active HTTP mux; prefer a plain path such as `/metrics` for compatibility. See the [HTTP API](/api/) for methods and response semantics.

## Actions and Logging

| Flag | Default | Purpose |
|:---|:---|:---|
| `-D`, `--[no-]dry-run` | `false` | Validate and print collector definitions without connecting to the target |
| `-E`, `--[no-]explain` | `false` | Connect, print the main target’s selected collectors, then exit |
| `--log.level=LEVEL` | `info` | `debug`, `info`, `warn`, or `error` |
| `--log.format=FORMAT` | `logfmt` | `logfmt` or `json` |
| `--version` | — | Print version, Go version, OS, and architecture |
| `-h`, `--help` | — | Print command help |

These action, logging, and exporter-toolkit web flags are command-line options;
they do not have `PG_EXPORTER_*` aliases in the stable release. Use
`--explain --fail-fast` to require a successful target precheck. `--dry-run` checks
collector definitions; a running scrape also checks permissions, result columns,
and output values. Startup and reload also check constant-label conflicts. Logs
go to standard error.

## Examples

```bash
# Same-host PostgreSQL using libpq defaults
pg_exporter --config=/etc/pg_exporter.yml

# Remote target without putting the password on the command line
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full'
pg_exporter --web.listen-address=:9630

# Inspect collector definitions without starting the server
pg_exporter --config=./pg_exporter.yml --dry-run

# Add only these two discovered databases to the main target
pg_exporter --auto-discovery --include-database=app,analytics
```

Continue with [Production Deployment](/deploy/) for systemd, containers,
credentials, and Prometheus integration.
