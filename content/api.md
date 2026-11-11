---
title: "HTTP API"
linkTitle: "HTTP API"
description: "Metrics, health, role-routing, reload, explain, statistics, and version endpoints"
weight: 110
icon: fa-solid fa-plug
categories: [Reference]
---

`pg_exporter` serves metrics, health checks, and management endpoints on `:9630` by default. This reference describes stable **v{{< param version >}}**. Set the address with `--web.listen-address`; see [Command Reference](/cmd/).

| Endpoint | Method | Result |
|:---|:---|:---|
| [`/metrics`](#get-metrics) | GET | Prometheus metrics; change the path with `--web.telemetry-path` |
| [`/up`](#health-checks) | GET, HEAD | Main target availability; aliases `/health`, `/liveness`, `/readiness`, `/read` |
| [`/primary`](#traffic-routing) | GET, HEAD | Primary role; aliases `/leader`, `/master`, `/read-write`, `/rw` |
| [`/replica`](#traffic-routing) | GET, HEAD | Replica role; aliases `/standby`, `/slave`, `/read-only`, `/ro` |
| [`/reload`](#operational-endpoints) | GET, POST | Reload collector configuration |
| [`/explain`](#get-explain) | GET | Selected collectors for the main target, as plain text |
| [`/stat`](#get-stat) | GET | Collector statistics for the main target, as plain text |
| [`/version`](#get-version) | GET | Version and build information, as plain text |
| `/` | GET | HTML page with a link to metrics |
{.full-width}

The table lists the intended methods. Only `/reload` explicitly rejects other methods. Unmatched paths reach the root page, so use the documented paths for probes.

## Metrics Endpoint {#metrics-endpoint}

### GET /metrics {#get-metrics}

Each request collects metrics from the main target and any discovered databases. Collectors with a valid cache return their cached results.

```bash
curl -fsS http://127.0.0.1:9630/metrics
```

Example output:

```prometheus
# HELP pg_up last scrape was able to connect to the server: 1 for yes, 0 for no
# TYPE pg_up gauge
pg_up 1
# HELP pg_version server version number
# TYPE pg_version gauge
pg_version 180000
# HELP pg_in_recovery server is in recovery mode? 1 for yes 0 for no
# TYPE pg_in_recovery gauge
pg_in_recovery 0
```

A database failure can still produce HTTP 200 with `pg_up 0`. Check the metrics as well as the HTTP status. Non-fatal collector errors omit that collector’s results; other collectors continue. A fatal collector error stops further collection on that database. HTTP 500 indicates a gathering or encoding error, such as conflicting metric definitions.

Since v1.6.0, at most two metrics requests are admitted across collection, waiting, and response writing. Collection is serial; the second request waits within its remaining budget, and further requests receive HTTP 503. The budget is 30 seconds, shortened by a valid positive finite `X-Prometheus-Scrape-Timeout-Seconds` header. A canceled waiter executes no SQL.

Cancellation stops work before the next collector or database. A started collector with a positive timeout finishes its predicate chain and main SQL within their shared deadline and caches the result normally. A negative timeout removes that deadline: the query then follows request cancellation. An interrupted collection returns 503 if the connection still permits a response. Driver/network delays mean these deadlines are not hard wall-clock limits; configure the DSN `connect_timeout` for connection handshakes.

An interrupted pass does not increment `pg_exporter_scrape_error_count` or `pg_exporter_server_scrape_error_count`; its summary log is INFO `interrupted`. Query errors and fatal-query ERROR logs remain observable. A real failure coinciding with request cancellation can therefore be omitted from these two pass counters. Without request cancellation, connection/precheck failures and fatal query failures, including their own timeouts, retain their error accounting. Non-fatal failures remain query-level errors.

Failed refreshes retain the existing failure TTL. In particular, canceling a negative-timeout fatal collector caches a fatal failure: a later live scrape can count that failure and report `pg_up 0` until a successful refresh. Keep a positive timeout on fatal collectors. See [scrape lifetime](/design/scrape-lifetime/) for the rationale.

### Self-Monitoring Metrics {#self-monitoring-metrics}

The default built-in prefix is `pg` for PostgreSQL and `pgbouncer` for PgBouncer. `--namespace` changes this prefix. Invalid prefixes are rejected at startup. It does not change names defined in YAML.

| Metric | Type | Labels | Meaning |
|:---|:---|:---|:---|
| `pg_up` | Gauge | — | Main target availability from collection; see the interruption rule below |
| `pg_version` | Gauge | — | Main target’s version number |
| `pg_in_recovery` | Gauge | — | 1 for a replica, 0 for a primary; use when `pg_up = 1` |
| `pg_exporter_build_info` | Gauge | version, revision, branch, builddate, goversion, goos, goarch | Constant 1 with build metadata |
| `pg_exporter_up` | Gauge | — | Constant 1 |
| `pg_exporter_uptime` | Gauge | — | Seconds since exporter initialization |
| `pg_exporter_scrape_total_count` | Counter | — | Collection passes |
| `pg_exporter_scrape_error_count` | Counter | — | Passes where the main target had a connection or fatal collector error |
| `pg_exporter_scrape_duration` | Gauge | — | Last complete collection duration, in seconds |
| `pg_exporter_last_scrape_time` | Gauge | — | Unix timestamp at the end of the last collection |
| `pg_exporter_server_scrape_duration` | Gauge | datname | Last database scrape duration, in seconds |
| `pg_exporter_server_scrape_total_seconds` | Gauge | datname | Accumulated database scrape time, in seconds |
| `pg_exporter_server_scrape_total_count` | Gauge | datname | Database collection passes |
| `pg_exporter_server_scrape_error_count` | Gauge | datname | Database connection or fatal collector errors |
| `pg_exporter_query_scrape_total_count` | Gauge | datname, query | Collector calls, including cache hits and predicate skips |
| `pg_exporter_query_scrape_error_count` | Gauge | datname, query | Collector calls that reported an error |
| `pg_exporter_query_scrape_hit_count` | Gauge | datname, query | Result-cache hits |
| `pg_exporter_query_scrape_metric_count` | Gauge | datname, query | Samples in the current collector result |
| `pg_exporter_query_scrape_duration` | Gauge | datname, query | Last actual execution duration, in seconds; retained on cache hits |
| `pg_exporter_query_scrape_predicate_skip_count` | Gauge | datname, query | Calls skipped by a false, NULL, or empty predicate result |
| `pg_exporter_query_cache_ttl` | Gauge | datname, query | Remaining result-cache lifetime, in seconds |
{.full-width .wide .expand}

Configured constant labels are added to these series. On `pg_exporter_build_info`, the reserved `version`, `revision`, `branch`, `builddate`, `goversion`, `goos`, and `goarch` values take precedence over user labels. Invalid labels on per-database or per-query internal samples are warned about and skipped instead of causing a panic. Cumulative per-database and per-query counts are exposed as Gauges. Query statistics reset when the server is replanned, including after a reload. Database statistics reset when its connection object is recreated.

`--disable-intro` hides all built-in metrics in this table, including `pg_up`. YAML metrics, Go/process metrics, and HTTP health checks remain available.

During interruption, `pg_up` preserves the previous main-target availability, or 1 if this pass completed its precheck. If the very first precheck is interrupted before success, it remains 0 until a later successful scrape. Child-database interruptions follow the same per-server rule and do not increment the main-target error counter.

## Health Checks {#health-checks}

### GET /up {#get-up}

After initialization, only the once-per-second background health probe updates the HTTP health snapshot. Slow collection does not hold the probe lock, and completing a scrape cannot overwrite a newer probe result. HTTP health requests read the snapshot without executing SQL. `pg_up` and `pg_in_recovery` remain scrape metrics: a fatal collector can make `pg_up` zero while `/up` still returns 200 for a reachable database. The main PostgreSQL pool allows three connections, PgBouncer two, and each discovered database one.

| State in response body | HTTP status | Meaning |
|:---|:---|:---|
| `primary` | 200 | Target is reachable and is not in recovery |
| `replica` | 200 | Target is reachable and is in recovery |
| `starting` | 503 | PostgreSQL returned SQLSTATE `57P03` during the health probe |
| `down` | 503 | Target probe failed |
| `unknown` | 503 | Health state is not available yet |

```bash
curl -i http://127.0.0.1:9630/up
```

`/health`, `/liveness`, `/readiness`, and `/read` use the same handler. They test the database target, not just the exporter process. For Kubernetes, use a TCP liveness probe and an HTTP readiness probe if database downtime should remove readiness without restarting the exporter:

```yaml
livenessProbe:
  tcpSocket: { port: 9630 }
  initialDelaySeconds: 5
  periodSeconds: 10
readinessProbe:
  httpGet: { path: /readiness, port: 9630 }
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Traffic Routing {#traffic-routing}

Role checks use `pg_is_in_recovery()` from the main PostgreSQL target. They report role and reachability; they do not test application permissions or transaction read-only settings.

| Cached state | `/primary` | `/replica` | `/read` |
|:---|:---|:---|:---|
| `primary` | 200 | 404 | 200 |
| `replica` | 404 | 200 | 200 |
| `down`, `starting`, `unknown` | 503 | 503 | 503 |

The response body contains the state name. In PgBouncer mode, a successful `SHOW VERSION` probe maps to `primary`; it does not identify the role of PostgreSQL servers behind the pooler. Use exporters connected directly to PostgreSQL for role routing.

Each health response derives its HTTP code and body from one atomic status snapshot. This fixes contradictory responses during concurrent state changes; the state is still cached. Telemetry-path validation also verifies that requests reach the metrics handler under the active HTTP mux. Prefer an unescaped path such as `/metrics` for compatibility with the older mux.

### GET /primary {#get-primary}

Aliases: `/leader`, `/master`, `/read-write`, `/rw`.

### GET /replica {#get-replica}

Aliases: `/standby`, `/slave`, `/read-only`, `/ro`.

### GET /read {#get-read}

Alias of `/up`; accepts either PostgreSQL role.

### HAProxy Example {#haproxy-example}

Run an exporter beside each PostgreSQL instance. Send client traffic to port 5432 and health checks to port 9630:

```haproxy
backend pg_primary
  mode tcp
  option httpchk GET /primary
  http-check expect status 200
  server pg1 10.0.0.1:5432 check port 9630 inter 3000 fall 2 rise 2
  server pg2 10.0.0.2:5432 check port 9630 inter 3000 fall 2 rise 2

backend pg_replicas
  mode tcp
  balance roundrobin
  option httpchk GET /replica
  http-check expect status 200
  server pg1 10.0.0.1:5432 check port 9630 inter 3000 fall 2 rise 2
  server pg2 10.0.0.2:5432 check port 9630 inter 3000 fall 2 rise 2
```

Use `/read` instead of `/replica` to send read traffic to either role.

## Operational Endpoints {#operational-endpoints}

### GET /reload / POST /reload {#get-reload--post-reload}

Use POST to reload the selected configuration file or directory:

```bash
curl -fsS -X POST http://127.0.0.1:9630/reload
```

| HTTP status | Response | Meaning |
|:---|:---|:---|
| 200 | `server reloaded` | New definitions applied; queries are replanned on the next scrape |
| 500 | `fail to reload: ...` | Reload rejected; previous definitions remain active |
| 405 | `method not allowed` | Use GET or POST; response includes `Allow: GET, POST` |

Reload replaces collector definitions, clears their caches and query statistics, and invalidates plans. It does not execute the new SQL. An empty YAML file is valid and replaces the plan with zero configured collectors; built-in metrics remain. A rejected single-file reload preserves the previous definitions. Scrape `/metrics` after reloading and check collector errors. A configuration directory can skip invalid files while loading valid ones; inspect the log for `skip config` warnings.

On Unix, `SIGHUP` and `SIGUSR1` also reload configuration. `SIGTERM` terminates the process without waiting for active HTTP requests to finish. Restart the process to change the connection URL, labels, tags, or listen address. Restrict management access with a firewall, reverse proxy, or `--web.config.file`; see [Security](/security/).

### GET /explain {#get-explain}

Returns plain-text definitions of the main target’s selected collectors, including SQL, tags, TTL, timeout, and metric mappings. The output is empty before the first plan and immediately after a reload. Scrape first:

```bash
curl -fsS http://127.0.0.1:9630/metrics >/dev/null
curl -fsS http://127.0.0.1:9630/explain
```

This endpoint does not run PostgreSQL `EXPLAIN`, evaluate predicates, list rejected branches, or include discovered-database plans. Use debug logs for branch rejection reasons. To inspect a different database’s plan, run `pg_exporter --explain --fail-fast --url=...` against that database.

### GET /stat {#get-stat}

Returns a plain-text table for collectors selected for the main target:

```bash
curl -fsS http://127.0.0.1:9630/stat
```

```text
name                     total      hit        error      skip       metric     ttl/s  duration/ms
pg                       12         0          0          0          15         1      4.231000
pg_db                    12         11         0          0          28         0      0.153000
```

`total` counts collector calls, `hit` counts cache hits, `error` counts failed calls, and `skip` counts predicate skips. `metric` is the current sample count. `ttl/s` is remaining cache lifetime, truncated to an integer. `duration/ms` is the last actual execution time. Use the `pg_exporter_query_*` metrics to compare all discovered databases.

### GET /version {#get-version}

Returns version, revision, branch, Go version, build date, operating system, and architecture:

```bash
curl -fsS http://127.0.0.1:9630/version
```

Use this endpoint to identify the running binary when checking a deployment.
