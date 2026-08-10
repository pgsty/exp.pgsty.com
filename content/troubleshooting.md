---
title: "Troubleshooting"
linkTitle: "Troubleshooting"
description: "A symptom-driven runbook for startup, connectivity, missing metrics, slow scrapes, reloads, and packaging"
weight: 70
icon: fa-solid fa-stethoscope
categories: [Guide]
---

Start by separating four layers: process, HTTP, database connectivity, and individual collectors. A running systemd unit only proves the process layer; `pg_up 1` proves the current target connection and fatal collector path; a successful Prometheus scrape proves the end-to-end HTTP path.

## Five-Minute Triage

```bash
# Process and logs
systemctl status pg_exporter --no-pager
journalctl -u pg_exporter -n 100 --no-pager

# HTTP and build identity
curl -fsS http://127.0.0.1:9630/version
curl -i http://127.0.0.1:9630/up

# Core metrics
curl -fsS http://127.0.0.1:9630/metrics \
  | grep -E '^(pg|pgbouncer)_(up|version|in_recovery) '

# Planning and runtime evidence
curl -fsS http://127.0.0.1:9630/explain
curl -fsS http://127.0.0.1:9630/stat
```

| Observation | Layer to investigate |
|:---|:---|
| Unit exits immediately | Arguments, config path, telemetry path, listen address, file permissions |
| Port answers but `/up` is 503 | Target URL, network, authentication, `pg_hba.conf`, TLS, startup probe state |
| `/up` is 200 but a metric family is absent | Dynamic plan, version/role/tags/predicates, auto-discovery, disabled collector |
| `/metrics` returns an error or Prometheus times out | Fatal collector, slow query, scrape timeout, label/schema mismatch |
| Exporter is healthy but Prometheus target is down | Prometheus address, scheme, auth, TLS, firewall, telemetry path |
{.full-width}

## Process Will Not Start

### `no valid config path`

The config search order is `--config`, `PG_EXPORTER_CONFIG`, `./pg_exporter.yml`, `/etc/pg_exporter.yml`, then `/etc/pg_exporter`. Confirm the file exists and is readable by the runtime user:

```bash
sudo -u prometheus test -r /etc/pg_exporter.yml
sudo -u prometheus /usr/bin/pg_exporter \
  --config=/etc/pg_exporter.yml \
  --dry-run >/dev/null
```

`--dry-run` parses and explains the raw configuration without needing a live database. A config directory is non-recursive and loads only `.yaml` / `.yml` files in alphabetic order; a duplicate top-level branch name from a later file overrides the earlier definition.

### Invalid telemetry path

Since v1.4.0, `--web.telemetry-path` must be a canonical literal path beginning with `/`. It cannot contain a query, fragment, Go ServeMux wildcard, or collide with built-in endpoints such as `/up`, `/reload`, or `/version`.

Use `/metrics` unless there is a concrete need to change it, and update the Prometheus `metrics_path` at the same time.

### Address already in use

```bash
lsof -nP -iTCP:9630 -sTCP:LISTEN
```

Stop the conflicting service or choose another `--web.listen-address`. Do not run two exporters on one address and assume one of them will win.

## `pg_up` Is 0 or `/up` Returns 503

Restart temporarily with debug logging and a redacted, explicit URL:

```bash
PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pg_exporter/ca.crt' \
pg_exporter --config=/etc/pg_exporter.yml --log.level=debug
```

Check, in order:

1. DNS and TCP reachability to the advertised host and port.
2. Database name and login role.
3. `pg_hba.conf` source address, authentication method, and reload state.
4. Password source: URL, `.pgpass`, or `PG_EXPORTER_URL_FILE`.
5. `.pgpass` mode `0600`, hostname match, and the actual runtime user's HOME.
6. TLS CA path, hostname, and `sslmode`.
7. Connection limit on the monitoring role and server-wide connection exhaustion.

The packaged service runs as `prometheus`; testing as your shell user can therefore succeed while the service fails.

Non-blocking startup is normal: while the target is unavailable, the HTTP server remains up and the background probe retries. Use `--fail-fast` only when the orchestrator should treat initial database unreachability as a process startup failure.

## Metrics Are Missing

Missing metrics are usually a planning decision, not a scrape bug. Inspect `/explain` and look for:

- server version outside `[min_version, max_version)`;
- primary/replica role mismatch;
- missing `extension:`, `schema:`, `dbname:`, or `username:` fact;
- missing custom tag or matching `not:` tag;
- predicate query returning false;
- `skip: true`;
- database excluded from auto-discovery.

With auto-discovery enabled, the default exclusion is `template0,template1,postgres`. If metrics expected from `postgres` are absent, change `PG_EXPORTER_EXCLUDE_DATABASE` intentionally rather than assuming all databases are scraped.

## One Collector Fails

Use `/stat` and exporter self-metrics to identify the exact collector and database:

```promql
pg_exporter_query_scrape_error_count > 0
```

Common causes include:

- monitoring role lacks access to an optional view or function;
- extension/schema exists in a different database;
- custom SQL result columns do not match the YAML `metrics` list;
- a configured `LABEL` column is absent (v1.4.1 rejects the whole collector result atomically);
- the query exceeds its timeout;
- an extension or pre-release PostgreSQL view changed shape.

Run the collector SQL manually as the monitoring user in the same database. Preserve the result column names exactly, including zero-row result schemas.

## Scrapes Are Slow or Time Out

`/stat` reports last durations and errors per collector. Prometheus self-metrics provide the same evidence by `datname` and query name.

Typical remedies:

1. Optimize or narrow the SQL.
2. Increase `ttl` so expensive results are reused across scrapes.
3. Set a realistic per-query `timeout` below the Prometheus scrape timeout.
4. Disable optional high-cost collectors with `skip: true`.
5. Reduce database auto-discovery scope with `include-database` / `exclude-database`.
6. Control per-object metric cardinality on databases with thousands of tables or indexes.

Do not merely raise Prometheus `scrape_timeout` until it hides an unbounded query. A full scrape must fit comfortably inside both the timeout and scrape interval.

## Reload Fails

```bash
curl -i -X POST http://127.0.0.1:9630/reload
```

- `200`: the new query set was parsed, validated, installed, and existing plans were invalidated.
- `500`: the response contains the parse, schema, label-conflict, or config-path error. The old active query set remains in place.
- `405`: use GET or POST; POST is recommended.

Process-level options are not reloadable. Changes to listen addresses, target URL, logging, HTTP TLS/auth, namespace, or discovery flags require a service restart. Collector YAML can also be reloaded with `SIGHUP`; Unix builds additionally accept `SIGUSR1`.

## Docker and Package Pitfalls

| Symptom | Likely cause and fix |
|:---|:---|
| TLS verification fails in Docker | `scratch` image has no CA bundle; mount the CA and set `sslrootcert` |
| `.pgpass` is ignored in packaged service | Create `/var/lib/prometheus`, own it by `prometheus`, and use mode `0600` on `.pgpass` |
| RPM automation cannot find v1.4.1 artifact | Artifact prefix changed from `pg_exporter` to `pg-exporter` |
| Config edits disappear after container replacement | Mount `/etc/pg_exporter.yml` from durable configuration |
| Container cannot reach host PostgreSQL | `localhost` means the container; use the database service DNS name or an explicit host route |
{.full-width}

## Evidence to Include in a Bug Report

- `pg_exporter /version` output and installation method
- Operating system and architecture
- PostgreSQL or PgBouncer exact version
- Redacted target URL (retain scheme, host class, port, database, and `sslmode`)
- Relevant collector YAML and SQL, with secrets removed
- Debug log around the failure
- `/explain` and `/stat` entries for the collector
- Whether the problem reproduces with the bundled v{{< param version >}} config

Open an issue at [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter/issues) only after removing passwords, certificates, customer identifiers, and sensitive SQL text.
