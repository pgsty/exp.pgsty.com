---
title: "Troubleshooting"
linkTitle: "Troubleshooting"
description: "A symptom-driven runbook for startup, connectivity, missing metrics, slow scrapes, reloads, and packaging"
weight: 70
icon: fa-solid fa-stethoscope
categories: [Guide]
---

Check the process, HTTP access, database connection, then the failing collector. `pg_up 1` means the last scrape reached the main target and completed its fatal collectors. Other collectors or discovered databases can still have errors.

## Initial Checks {#initial-checks}

```bash
# Process and logs
systemctl status pg_exporter --no-pager
journalctl -u pg_exporter -n 100 --no-pager

# HTTP response and version
curl -fsS http://127.0.0.1:9630/version
curl -i http://127.0.0.1:9630/up

# Core metrics
curl -fsS http://127.0.0.1:9630/metrics \
  | grep -E '^(pg|pgbouncer)_(up|version|in_recovery)(\{| )'

# Collection plan and runtime statistics
curl -fsS http://127.0.0.1:9630/explain
curl -fsS http://127.0.0.1:9630/stat
```

| Observation | Layer to investigate |
|:---|:---|
| Unit exits immediately | Arguments, config path, telemetry path, listen address, file permissions |
| Port answers but `/up` is 503 | Target URL, network, authentication, `pg_hba.conf`, TLS, startup probe state |
| `/up` is 200 but a metric family is absent | Dynamic plan, version/role/tags/predicates, auto-discovery, disabled collector |
| `/metrics` returns an error or Prometheus times out | Slow query, scrape timeout, duplicate or invalid metric samples |
| Exporter is healthy but Prometheus target is down | Prometheus address, scheme, auth, TLS, firewall, telemetry path |
{.full-width}

## Process Will Not Start {#process-will-not-start}

### `no valid config path` {#no-valid-config-path}

The config search order is `--config`, `PG_EXPORTER_CONFIG`, `./pg_exporter.yml`, `/etc/pg_exporter.yml`, then `/etc/pg_exporter`. Confirm the file exists and is readable by the runtime user:

```bash
sudo -u prometheus test -r /etc/pg_exporter.yml
sudo -u prometheus /usr/bin/pg_exporter \
  --config=/etc/pg_exporter.yml \
  --dry-run >/dev/null
```

`--dry-run` parses and explains the raw configuration without needing a live database. A config directory is non-recursive and loads only `.yaml` / `.yml` files in alphabetic order; a duplicate top-level branch name from a later file overrides the earlier definition.

### Invalid telemetry path {#invalid-telemetry-path}

Since v1.4.0, `--web.telemetry-path` must be a canonical literal path beginning with `/`. It cannot contain a query, fragment, Go ServeMux wildcard, or collide with built-in endpoints such as `/up`, `/reload`, or `/version`.

Use `/metrics` unless there is a concrete need to change it, and update the Prometheus `metrics_path` at the same time.

### Address already in use {#address-already-in-use}

```bash
lsof -nP -iTCP:9630 -sTCP:LISTEN
```

Stop the conflicting service or choose another `--web.listen-address`.

## `pg_up` Is 0 or `/up` Returns 503 {#pg_up-is-0-or-up-returns-503}

For the packaged service, add `--log.level=debug` to `PG_EXPORTER_OPTS` in `/etc/default/pg_exporter`, then restart the service. This preserves its user and connection settings:

```bash
sudo systemctl restart pg_exporter
sudo journalctl -u pg_exporter -f
```

For a foreground process, use the real target URL and supply the password through `.pgpass` or a secret file:

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
8. `--connect-timeout`: the default is 100 ms for connection and metadata probes. Increase it if normal network latency exceeds this budget.

After diagnosis, restore `--log.level=info` and restart the service.

The packaged service runs as `prometheus`; testing as your shell user can therefore succeed while the service fails.

Non-blocking startup is normal: while the target is unavailable, the HTTP server remains up and the background probe retries. Use `--fail-fast` only when the orchestrator should treat initial database unreachability as a process startup failure.

## Metrics Are Missing {#metrics-are-missing}

Scrape `/metrics` once to build the plan. `/explain` shows collectors selected for the main target. For a missing collector, compare its YAML with the target version, role, and tags; debug logs report why a branch was rejected. Check for:

- server version outside `[min_version, max_version)`;
- primary/replica role mismatch;
- missing `extension:`, `schema:`, `dbname:`, or `username:` fact;
- missing custom tag or matching `not:` tag;
- predicate query returning false;
- `skip: true`;
- database excluded from auto-discovery.

The include/exclude lists apply to additional discovered databases. The database in the connection URL is always monitored, even if its name appears in the default exclusion `template0,template1,postgres`. Predicates can skip a selected collector, and a successful query can return no rows; check `/stat` and the SQL result as well.

## One Collector Fails {#one-collector-fails}

Use `/stat` for the main target. Use exporter self-metrics, labeled by `datname` and `query`, for all monitored databases:

```promql
pg_exporter_query_scrape_error_count > 0
```

This value counts errors since the last plan was built; a nonzero value can describe an earlier failure. Scrape again and check whether it increases. Read the log for the error text.

Common causes include:

- monitoring role lacks access to an optional view or function;
- extension/schema exists in a different database;
- custom SQL result columns do not match the YAML `metrics` list;
- a configured `LABEL` column is absent (the exporter emits no metrics from that collector for this call);
- the query exceeds its timeout;
- an extension or pre-release PostgreSQL view changed shape.

Run the collector SQL manually as the monitoring user in the same database. Preserve the result column names exactly, including zero-row result schemas.

## Scrapes Are Slow or Time Out {#scrapes-are-slow-or-time-out}

Since v1.6.0, at most two metrics requests are admitted across collection, waiting, and response writing. Collection is serial; the second request waits within its remaining budget, and further requests receive HTTP 503. The budget is 30 seconds, shortened by a valid positive finite `X-Prometheus-Scrape-Timeout-Seconds` header. A canceled waiter executes no SQL.

Cancellation stops work before the next collector or database. A started collector with a positive timeout finishes its predicate chain and main SQL within their shared deadline and caches the result normally. A negative timeout removes that deadline: the query then follows request cancellation. An interrupted collection returns 503 if the connection still permits a response. Driver/network delays mean these deadlines are not hard wall-clock limits; configure the DSN `connect_timeout` for connection handshakes.

An interrupted pass does not increment `pg_exporter_scrape_error_count` or `pg_exporter_server_scrape_error_count`; its summary log is INFO `interrupted`. Query errors and fatal-query ERROR logs remain observable. A real failure coinciding with request cancellation can therefore be omitted from these two pass counters. Without request cancellation, connection/precheck failures and fatal query failures, including their own timeouts, retain their error accounting. Non-fatal failures remain query-level errors.

Failed refreshes retain the existing failure TTL. In particular, canceling a negative-timeout fatal collector caches a fatal failure: a later live scrape can count that failure and report `pg_up 0` until a successful refresh. Keep a positive timeout on fatal collectors. See [scrape lifetime](/design/scrape-lifetime/) for the rationale.

`/stat` reports query durations in milliseconds for the main target. `pg_exporter_query_scrape_duration` reports seconds for each `datname` and `query`. Error counts are available in both; error text is in the logs.

Typical remedies:

1. Optimize or narrow the SQL.
2. Increase `ttl` so expensive results are reused across scrapes.
3. Set a realistic per-query `timeout` below the Prometheus scrape timeout.
4. Disable optional high-cost collectors with `skip: true`.
5. Reduce database auto-discovery scope with `include-database` / `exclude-database`.
6. Control per-object metric cardinality on databases with thousands of tables or indexes.

Queries and discovered databases are scraped sequentially, so budget for their combined duration. Keep the full scrape below Prometheus `scrape_timeout` and `scrape_interval`. The HTTP server also has a 30-second write timeout.

## Reload Fails {#reload-fails}

```bash
curl -i -X POST http://127.0.0.1:9630/reload
```

- `200`: the new configuration passed validation and was loaded; the next scrape will rebuild the collection plans.
- `500`: the response contains the parse, schema, label-conflict, or config-path error. The old active query set remains in place.
- `405`: use GET or POST; POST is recommended.

Restart the service after changing the target URL, listen address, logging, namespace, discovery flags, or the path passed to `--web.config.file`. Exporter-toolkit reads the contents of that web configuration file dynamically; certificate or Basic Auth changes at the same path do not use `/reload`.

Collector YAML can also be reloaded with `SIGHUP`; Unix builds additionally accept `SIGUSR1`. A reload rebuilds plans on the next scrape and resets per-query statistics.

## Docker and Package Pitfalls {#docker-and-package-pitfalls}

| Symptom | Likely cause and fix |
|:---|:---|
| TLS verification fails in Docker | v1.6.0 includes public CA roots; check hostname/trust and mount your private CA with `sslrootcert` when needed |
| `.pgpass` is ignored in packaged service | Check the `prometheus` account home or `PGPASSFILE`; give the service user ownership and use mode `0600` |
| RPM automation cannot find v1.4.1 artifact | Artifact prefix changed from `pg_exporter` to `pg-exporter` |
| Config edits disappear after container replacement | Mount `/etc/pg_exporter.yml` from durable configuration |
| Container cannot reach host PostgreSQL | `localhost` means the container; use the database service DNS name or an explicit host route |
{.full-width}

## Evidence to Include in a Bug Report {#evidence-to-include-in-a-bug-report}

- `pg_exporter --version` or `curl http://127.0.0.1:9630/version` output, and installation method
- Operating system and architecture
- PostgreSQL or PgBouncer exact version
- Redacted target URL (retain scheme, host class, port, database, and `sslmode`)
- Relevant collector YAML and SQL, with secrets removed
- Debug log around the failure
- `/explain` and `/stat` entries for the collector
- Whether the problem reproduces with the bundled v{{< param version >}} config

Remove passwords, private keys, customer identifiers, and sensitive SQL text, then submit the evidence to [pgsty/pg_exporter Issues](https://github.com/pgsty/pg_exporter/issues).
