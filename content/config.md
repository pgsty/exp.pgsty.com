---
title: "Collector Configuration"
linkTitle: "Configuration"
description: "Complete reference for the declarative YAML collector format and execution model"
weight: 90
icon: fa-solid fa-code
categories: [Reference]
---

A YAML **collector** defines a SQL query, its metrics, and when to run it. This page describes the configuration used by stable **v{{< param version >}}**. For process flags and environment variables, see [Command Reference](/cmd/).

Load one YAML file or a directory of YAML files. The default `pg_exporter.yml` combines 57 collector files and one schema reference from [`config/`](https://github.com/pgsty/pg_exporter/tree/v1.5.0/config).

## Configuration Loading

PG Exporter searches for configuration in the following order:

1. Command-line argument: `--config=/path/to/config`
2. Environment variable: `PG_EXPORTER_CONFIG=/path/to/config`
3. Current directory: `./pg_exporter.yml`
4. System config file: `/etc/pg_exporter.yml`
5. System config directory: `/etc/pg_exporter/`

Directory mode details:

- Only `.yml` / `.yaml` files in that directory are loaded, non-recursively
- Files are merged in lexicographic order; later files override earlier collector definitions with the same top-level name
- Invalid files are skipped with a warning when other files provide valid collectors. A directory with YAML files but no valid collector definitions returns an error
- The selected file or directory is the complete configuration. It is not merged with another standard path. An explicit path that fails to load does not fall back to the defaults

## Simple Gauge Collector

Set `PG_EXPORTER_URL` with your target and credentials as shown in [Quick Start](/start/#run-and-verify). Save the following definition as `connections.yml`. It exports the total connection count and the counts by state.

```yaml
pg_connections:
  desc: "Instance connections"
  query: |
    SELECT
      count(*) as total,
      count(*) FILTER (WHERE state = 'active') as active,
      count(*) FILTER (WHERE state = 'idle') as idle,
      count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
    FROM pg_stat_activity
    WHERE pid != pg_backend_pid()
  tags: [cluster]
  ttl: 1
  metrics:
    - total: {usage: GAUGE, description: "Total connections"}
    - active: {usage: GAUGE, description: "Active connections"}
    - idle: {usage: GAUGE, description: "Idle connections"}
    - idle_in_transaction: {usage: GAUGE, description: "Idle in transaction"}
```

Validate the configuration, then run a foreground process:

```bash
pg_exporter --dry-run --config=./connections.yml
pg_exporter --config=./connections.yml
```

Check the output in another terminal:

```bash
curl -fsS http://127.0.0.1:9630/metrics | grep '^pg_connections_'
```

This file contains only the example collector. To add metrics to the default configuration, see [Custom Collectors](#custom-collectors).

## Collector Structure

Each top-level key identifies one collector branch. This example shows the available fields; replace the SQL and column names with those for your query:

```yaml
collector_branch_name:           # Unique identifier for this collector
  name: metric_namespace         # Metric prefix (defaults to branch name)
  desc: "Collector description"  # Human-readable description
  query: |                       # SQL query to execute
    SELECT column1, column2
    FROM table

  # Execution Control
  priority: 100                  # Lower values run first within each fatal/non-fatal group
  ttl: 10                        # Cache time-to-live in seconds
  timeout: 0.1                   # Query timeout in seconds
  fatal: false                   # If true, error stops this database’s collection
  skip: false                    # If true, collector is disabled

  # Version Compatibility
  min_version: 100000            # Minimum PostgreSQL version (inclusive)
  max_version: 999999            # Maximum PostgreSQL version (exclusive)

  # Execution Tags
  tags: [cluster, primary]       # Conditions for execution

  # Predicate Queries (optional)
  predicate_queries:
    - name: "check_function"
      ttl: 60                    # Independent predicate-result cache, in seconds
      predicate_query: |
        SELECT EXISTS (...)

  # Metric Definitions
  metrics:
    - column_name:
        usage: GAUGE             # GAUGE, COUNTER, HISTOGRAM, LABEL, or DISCARD
        rename: metric_name      # Optional: rename the metric
        description: "Help text" # Metric description
        default: 0               # Default value if NULL
        scale: 1000              # Scale factor for the value
        # For usage: HISTOGRAM, also specify bucket: [1, 10, 100]
```

Validation rules:

- `query` and each `predicate_query` must contain SQL. Main and predicate TTL values must be zero or positive
- Each entry in `metrics` must define exactly one column mapping, with a unique source column name
- Each collector must expose at least one `GAUGE`, `COUNTER`, or `HISTOGRAM` column
- `usage` accepts `GAUGE`, `COUNTER`, `HISTOGRAM`, `LABEL`, or `DISCARD`, without case sensitivity
- `HISTOGRAM` columns must define `bucket`: a finite, strictly increasing list of bucket upper bounds; the `+Inf` bucket is appended automatically
- Metric names and label names are validated against Prometheus naming rules during load; invalid configs fail fast
- At startup and reload, constant labels are checked against query labels. With built-in metrics enabled, `datname` and `query` are also reserved. If any configured collector uses `HISTOGRAM`, a constant label named `le` is rejected
- SQL results must include every `LABEL` and `HISTOGRAM` column, even for zero-row results. Missing either rejects the whole collector result. A missing `GAUGE` or `COUNTER` column is logged and omitted
- If you use one-line inline `metrics` definitions, keep `description` values double-quoted to avoid YAML ambiguity

## Core Configuration Elements

### Collector Branch Name

The top-level key identifies the branch; `name` sets its metric prefix:

```yaml
pg_stat_database:  # Must be unique
  name: pg_db      # Actual metric namespace
```

Branches for different server versions can share `name`. Their version ranges and tags must select at most one branch for the same metric series. The planner selects every eligible branch; it does not choose one winner for each name.

`priority` sets execution order, with lower values first. Fatal collectors run before non-fatal collectors. In directory mode, omitted priorities become `100 +` the successfully loaded file’s position. In a single file, an omitted priority stays zero. Set distinct priorities when order matters.

### Query Definition

The SQL query that retrieves metrics:

```yaml
query: |
  SELECT
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit
  FROM pg_stat_database
  WHERE datname NOT IN ('template0', 'template1')
```

### Metric Types

Declare each result column as a value, label, or discarded column. A scalar metric is named `<collector name>_<column name>`. Column `rename` replaces the metric suffix or label name; column `name` overrides the SQL column name used for lookup.

| Usage       | Description                                                      | Example                      |
|-------------|------------------------------------------------------------------|------------------------------|
| `GAUGE`     | Instantaneous value that can go up or down                       | Current connections          |
| `COUNTER`   | Cumulative value; resets when source statistics reset                             | Total transactions           |
| `HISTOGRAM` | Snapshot histogram deriving `_bucket` / `_count` / `_sum` series | Transaction age distribution |
| `LABEL`     | Use as a Prometheus label                                        | Database name                |
| `DISCARD`   | Ignore this column                                               | Internal values              |

### Histogram Columns (HISTOGRAM)

`HISTOGRAM`, available since v1.4.0, groups observations by their label values.
Each non-NULL value contributes one observation. The output consists of three
Gauge families: `<collector>_<column>_bucket`, `_count`, and `_sum`. Buckets are
cumulative within the current snapshot and include `le="+Inf"`:

```yaml
pg_xact_age:
  name: pg_xact_age
  desc: "Open transaction age distribution histogram"
  query: |
    SELECT datname,
           greatest(0, extract(epoch FROM now() - xact_start)) AS seconds
    FROM pg_stat_activity
    WHERE pid <> pg_backend_pid() AND backend_type = 'client backend'
      AND datname IS NOT NULL AND xact_start IS NOT NULL;
  ttl: 10
  min_version: 100000
  tags: [cluster]
  metrics:
    - datname: {usage: LABEL, description: "Database name"}
    - seconds:
        usage: HISTOGRAM
        bucket: [1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000]
        description: "Open transaction age snapshot in seconds"
```

Usage notes:

- The distribution is rebuilt when the collector refreshes its cache. All three
  families have type `gauge` and may decrease. Use `histogram_quantile()` directly
  on buckets; use the current `_sum / _count` for the mean. Do not apply `rate()`
  or `increase()` to these snapshot series
- SQL `NULL` observations are omitted unless `default` is set. A label group with
  no observations emits no histogram series. Invalid or non-finite observations
  reject the collector result
- `scale` is applied to the observation before bucket assignment; as with scalar
  columns, timestamp and boolean values are exempt from `scale`
- The [`pg_xact_age`](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0450-pg_xact_age.yml)
  collector in the default bundle serves as the reference implementation

For the example above, the 95th percentile is:

```promql
histogram_quantile(0.95, pg_xact_age_seconds_bucket)
```

### Cache Control (TTL)

The `ttl` parameter controls result caching:

```yaml
# Fast queries - minimal caching
pg_stat_activity:
  ttl: 1  # Cache for 1 second

# Expensive queries - longer caching
pg_table_bloat:
  ttl: 3600  # Cache for 1 hour
```

`ttl` defaults to 0, which refreshes on each scrape. Use a TTL longer than the
scrape interval to reduce SQL load. Choose it from the maximum acceptable age of
the metric. `--disable-cache` forces main-query refreshes.

A failed refresh clears the old result. The error or predicate-skip result remains
cached until the main TTL expires. Predicate results can have a separate TTL.

### Timeout Control

Prevent queries from running too long:

```yaml
timeout: 0.1   # 100 ms; also used when omitted or set to 0
timeout: 1.0   # 1 second
timeout: -1    # Disable this collector’s query deadline
```

The deadline covers predicate queries and the main query together. Set it above
normal execution time and below the scrape time budget. Connection prechecks use
the separate `--connect-timeout` flag, measured in milliseconds.

Cache TTLs and timeouts reject NaN, infinity, and positive values that overflow Go's `time.Duration`. Cache TTLs remain nonnegative; finite negative timeouts still disable the deadline.

### Version Compatibility

Control which PostgreSQL versions can run this collector:

```yaml
min_version: 100000  # PostgreSQL 10.0+
max_version: 140000  # Below PostgreSQL 14.0
```

`min_version` is inclusive; `max_version` is exclusive. An omitted or zero bound
leaves that end unrestricted. `skip` and `fatal` default to `false`.

Version numbers follow PostgreSQL `server_version_num` rules:

- `100000` = 10.0
- `130002` = 13.2
- `160001` = 16.1
- `190000` = 19.0
- `90600` = 9.6, relevant when using the legacy config bundle

## Execution Model

A collector passes through three steps:

1. **Plan:** on the first scrape or after plan invalidation, check target type, version, tags, and `skip`. Select every eligible branch. `/explain` shows selected collectors on the main target; debug logs show rejection reasons.
2. **Collect:** return a cached result while its TTL is valid. Otherwise, evaluate predicates and run the main SQL within the shared timeout. Convert the complete result to metrics before publishing it.
3. **Handle failure:** a normal collector error omits its result and increments its query error count. A fatal collector error stops further collection on that database and marks that database scrape as failed. A failure on the main target also sets `pg_up` to 0. Other discovered databases can still be collected.

Successful metadata prechecks also replan when the connected username, schema set, or extension set changes. New eligible collectors appear on the next scrape; removed dependencies stop selecting their collectors. Unchanged sets retain the plan and caches. Replanning resets query statistics and caches, as a reload does.

## Tag System

Tags control when and where collectors execute:

### Built-in Tags

| Tag                   | Description                         |
|-----------------------|-------------------------------------|
| `cluster`             | Run on the main connection only, not on auto-discovered database connections |
| `primary` / `master` / `leader`  | Only on primary servers             |
| `standby` / `replica` / `slave` | Only on replica servers             |
| `pgbouncer`           | Only for PgBouncer connections      |

`cluster` does not coordinate separate exporter processes or PostgreSQL instances.
All tags on a collector must match.

### Prefixed Tags

| Prefix       | Example                        | Description                 |
|--------------|--------------------------------|-----------------------------|
| `dbname:`    | `dbname:postgres`              | Only on specific database   |
| `username:`  | `username:monitor`             | Only with specific user     |
| `extension:` | `extension:pg_stat_statements` | Only if extension installed |
| `schema:`    | `schema:public`                | Only if schema exists       |
| `not:`       | `not:slow`                     | NOT when exporter has tag   |

### Custom Tags

Pass custom tags to the exporter:

```bash
pg_exporter --tag="production,critical"
```

Then use in configuration:

```yaml
expensive_metrics:
  tags: [critical]  # Only runs with 'critical' tag
```

## Predicate Queries

Execute conditional checks before main query:

```yaml
predicate_queries:
  - name: "Check pg_stat_statements"
    predicate_query: |
      SELECT EXISTS (
        SELECT 1 FROM pg_extension
        WHERE extname = 'pg_stat_statements'
      )
```

Each predicate must return one Boolean column. One row containing `true` passes;
`false`, NULL, or zero rows skips the main query. Multiple rows, a non-Boolean
column, or an SQL error fails the collector. All predicates must pass.

Add `ttl: 60` to a predicate to cache its pass/skip result for 60 seconds. The
default, 0, checks it whenever the main query refreshes. Errors are not stored in
the predicate cache. `--disable-cache` does not bypass predicate caches.

## Metric Definition

### Basic Definition

```yaml
metrics:
  - numbackends:
      usage: GAUGE
      description: "Number of backends connected"
```

### Advanced Options

```yaml
metrics:
  - checkpoint_write_time:
      usage: COUNTER
      rename: write_time        # Rename metric
      scale: 0.001              # Convert ms to seconds
      default: 0                # Use 0 if NULL
      description: "Checkpoint write time in seconds"
```

For `GAUGE` and `COUNTER`, SQL NULL becomes `NaN` unless `default` is set.
Numeric values and defaults are multiplied by `scale` (default 1). Timestamps
become Unix seconds and Booleans become 0 or 1; neither is scaled. A NULL label
becomes an empty string.

## Collector Organization

PG Exporter ships with pre-organized collectors:

| Range | Category      | Description                     |
|-------|---------------|---------------------------------|
| 0000   | Documentation | Examples and documentation      |
| 0100   | Basic         | Server info, settings, metadata |
| 0200   | Replication   | Replication, slots, receivers   |
| 0300   | Persistence   | I/O, checkpoints, recovery           |
| 0400   | Activity      | WAL, connections, locks, queries     |
| 0500   | Progress      | Vacuum, index creation progress |
| 0600   | Database      | Per-database statistics         |
| 0700   | Objects       | Tables, indexes, functions      |
| 0800   | Optional      | Expensive/optional metrics      |
| 0900   | PgBouncer     | Connection pooler metrics       |
| 1000+ | Extensions    | Extension-specific metrics      |
{.full-width .wide .expand}

## Real-World Examples

### Counter with Labels

```yaml
pg_table_stats:
  desc: "Table statistics"
  query: |
    SELECT
      current_database() AS datname,
      schemaname,
      relname AS tablename,
      n_tup_ins,
      n_tup_upd,
      n_tup_del,
      n_live_tup,
      n_dead_tup
    FROM pg_stat_user_tables
  ttl: 10
  metrics:
    - datname: {usage: LABEL}
    - schemaname: {usage: LABEL}
    - tablename: {usage: LABEL}
    - n_tup_ins: {usage: COUNTER, description: "Tuples inserted"}
    - n_tup_upd: {usage: COUNTER, description: "Tuples updated"}
    - n_tup_del: {usage: COUNTER, description: "Tuples deleted"}
    - n_live_tup: {usage: GAUGE, description: "Live tuples"}
    - n_dead_tup: {usage: GAUGE, description: "Dead tuples"}
```

### Version-Specific Collector

This example uses columns available on PostgreSQL 14–17. PostgreSQL 18 moves WAL
timing statistics to `pg_stat_io`; the bundled `pg_wal` collector has separate branches.

```yaml
pg_wal_stats:
  desc: "WAL statistics (PG 14–17)"
  min_version: 140000
  max_version: 180000
  query: |
    SELECT
      wal_records,
      wal_bytes,
      wal_buffers_full,
      wal_write_time,
      wal_sync_time
    FROM pg_stat_wal
  ttl: 10
  tags: [cluster]
  metrics:
    - wal_records: {usage: COUNTER}
    - wal_bytes: {usage: COUNTER}
    - wal_buffers_full: {usage: COUNTER}
    - wal_write_time: {usage: COUNTER, scale: 0.001}
    - wal_sync_time: {usage: COUNTER, scale: 0.001}
```

### Extension-Dependent Collector

This example requires the PostgreSQL 13+ `pg_stat_statements` schema and a search
path that contains the extension.

```yaml
pg_stat_statements_metrics:
  desc: "Query performance statistics"
  min_version: 130000
  tags: [cluster, "extension:pg_stat_statements"]
  query: |
    SELECT
      sum(calls) as total_calls,
      sum(total_exec_time) as total_time,
      sum(total_exec_time) / NULLIF(sum(calls), 0) as mean_time
    FROM pg_stat_statements
  ttl: 60
  metrics:
    - total_calls: {usage: COUNTER}
    - total_time: {usage: COUNTER, scale: 0.001}
    - mean_time: {usage: GAUGE, scale: 0.001}
```

## Custom Collectors

### Creating Your Own Metrics

1. To add metrics to the default configuration, first copy the complete configuration into a new directory:

```bash
sudo install -d -m 0755 /etc/pg_exporter
sudo cp -p /etc/pg_exporter.yml /etc/pg_exporter/0000-base.yml
```

If you already use a configuration directory, add the new file there. Save the application collector below as `/etc/pg_exporter/9990-app.yml`. It assumes the application tables exist and `processing_time` is a numeric value in seconds:

```yaml
# /etc/pg_exporter/9990-app.yml
app_metrics:
  desc: "Application-specific metrics"
  tags: ["dbname:app"]
  query: |
    SELECT
      (SELECT count(*) FROM users WHERE active = true) as active_users,
      (SELECT count(*) FROM orders WHERE created_at > NOW() - '1 hour'::interval) as recent_orders,
      (SELECT avg(processing_time) FROM jobs WHERE completed_at > NOW() - '5 minutes'::interval) as avg_job_time
  ttl: 30
  metrics:
    - active_users: {usage: GAUGE, description: "Currently active users"}
    - recent_orders: {usage: GAUGE, description: "Orders in last hour"}
    - avg_job_time: {usage: GAUGE, description: "Average job processing time"}
```

2. Set `PG_EXPORTER_URL` for the `app` database with the same credentials. Validate the definitions and select its collectors:

```bash
pg_exporter --dry-run --config=/etc/pg_exporter/
pg_exporter --explain --fail-fast --config=/etc/pg_exporter/
```

3. Run the exporter with the same URL and configuration, then request `/metrics`
   and inspect `/stat` from another terminal. `--explain` selects collectors but does
   not execute their SQL.

To switch a packaged service to this directory, set `PG_EXPORTER_CONFIG=/etc/pg_exporter` in `/etc/default/pg_exporter` and restart the service. For later YAML edits in that directory, use `POST /reload`.

### Conditional Metrics

Use predicate queries for conditional metrics:

```yaml
partition_metrics:
  desc: "Partitioned table metrics"
  predicate_queries:
    - name: "Check if partitioning is used"
      predicate_query: |
        SELECT EXISTS (
          SELECT 1 FROM pg_class
          WHERE relkind = 'p' LIMIT 1
        )
  query: |
    SELECT
      current_database() AS datname,
      ns.nspname AS schemaname,
      parent.relname AS parent_table,
      count(*) as partition_count,
      sum(pg_relation_size(child.oid)) as total_size
    FROM pg_inherits
    JOIN pg_class parent ON parent.oid = pg_inherits.inhparent
    JOIN pg_class child ON child.oid = pg_inherits.inhrelid
    JOIN pg_namespace ns ON ns.oid = parent.relnamespace
    WHERE parent.relkind = 'p'
    GROUP BY ns.nspname, parent.relname
  ttl: 300
  min_version: 100000
  metrics:
    - datname: {usage: LABEL}
    - schemaname: {usage: LABEL}
    - parent_table: {usage: LABEL}
    - partition_count: {usage: GAUGE}
    - total_size: {usage: GAUGE}
```

## Performance Optimization

Measure SQL duration with the monitoring role. Give expensive collectors a longer
TTL and enough timeout to complete under normal load. Set `skip: true` on
collectors you do not use. Add `tags: [cluster]` to instance-wide SQL so automatic
database discovery does not repeat it.

Keep labels bounded and include enough columns to identify each result row.
For example, table names need a database and schema when collecting several
databases. Prefer aggregated SQL when object-level series are not needed.

### Monitoring Collector Performance

Check collector execution statistics:

```bash
# View collector statistics (hit / error / skip counters and durations)
curl http://localhost:9630/stat

# Per-collector duration and error counters, by datname/query
curl -s http://localhost:9630/metrics | grep -E 'pg_exporter_query_scrape_(duration|error_count)'
```

## Troubleshooting Configuration

### Validate Configuration

```bash
# Dry run - shows parsed configuration
pg_exporter --dry-run

# Explain - shows planned queries
pg_exporter --explain
```

### Common Issues

| Problem           | Solution                                             |
|-------------------|------------------------------------------------------|
| Metrics missing   | Check tags and version compatibility                 |
| Slow scrapes      | Increase TTL, add timeout, disable expensive queries |
| High memory usage | Aggregate results or filter a defined set of objects                    |
| Permission errors | Verify query permissions for monitoring user         |

### Debug Logging

Enable debug logging to troubleshoot:

```bash
pg_exporter --log.level=debug
```
