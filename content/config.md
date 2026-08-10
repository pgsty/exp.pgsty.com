---
title: "Collector Configuration"
linkTitle: "Configuration"
description: "Complete reference for the declarative YAML collector format and execution model"
weight: 90
icon: fa-solid fa-code
categories: [Reference]
---

Every business metric in `pg_exporter` is driven by a YAML **collector** definition: one SQL query plus its execution conditions (version, role, tags, predicates) and runtime controls (caching, timeout). This page is the complete reference for collector definitions.

A configuration can be a single YAML file (like the default `pg_exporter.yml`) or a directory of YAML files — the official default bundle is merged from the 58 definition files under [`config/`](https://github.com/pgsty/pg_exporter/tree/main/config).

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
- If a config directory contains YAML files but every one of them fails to parse, the exporter returns an error instead of silently ignoring the directory

## Collector Structure

Each collector is a top-level object in the YAML configuration with a unique name and various properties:

```yaml
collector_branch_name:           # Unique identifier for this collector
  name: metric_namespace         # Metric prefix (defaults to branch name)
  desc: "Collector description"  # Human-readable description
  query: |                       # SQL query to execute
    SELECT column1, column2
    FROM table

  # Execution Control
  ttl: 10                        # Cache time-to-live in seconds
  timeout: 0.1                   # Query timeout in seconds
  fatal: false                   # If true, failure fails entire scrape
  skip: false                    # If true, collector is disabled

  # Version Compatibility
  min_version: 100000            # Minimum PostgreSQL version (inclusive)
  max_version: 999999            # Maximum PostgreSQL version (exclusive)

  # Execution Tags
  tags: [cluster, primary]       # Conditions for execution

  # Predicate Queries (optional)
  predicate_queries:
    - name: "check_function"
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
        bucket: [1, 10, 100]     # Bucket upper bounds for HISTOGRAM columns (strictly increasing, +Inf appended)
```

Validation rules:

- Each entry in `metrics` must define exactly one column mapping
- Each collector must expose at least one `GAUGE`, `COUNTER`, or `HISTOGRAM` column
- `usage` only accepts `GAUGE`, `COUNTER`, `HISTOGRAM`, `LABEL`, or `DISCARD`
- `HISTOGRAM` columns must define `bucket`: a finite, strictly increasing list of bucket upper bounds; the `+Inf` bucket is appended automatically
- Metric names and label names are validated against Prometheus naming rules during load; invalid configs fail fast
- Constant labels are checked for conflicts during load; they cannot overlap with query labels or built-in dynamic labels such as `datname` and `query`; when any `HISTOGRAM` collector is configured, `le` is reserved and cannot be used as a constant label
- The SQL result must include every column declared as `LABEL`; since `v1.4.1`, a missing label column fails that collector's entire scrape instead of emitting an empty label or retaining stale results, while other non-fatal collectors continue normally
- If you use one-line inline `metrics` definitions, keep `description` values double-quoted to avoid YAML ambiguity

## Core Configuration Elements

### Collector Branch Name

The top-level key uniquely identifies a collector across the entire configuration:

```yaml
pg_stat_database:  # Must be unique
  name: pg_db      # Actual metric namespace
```

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

Each column in the query result must be mapped to a metric type:

| Usage       | Description                                                      | Example                      |
|-------------|------------------------------------------------------------------|------------------------------|
| `GAUGE`     | Instantaneous value that can go up or down                       | Current connections          |
| `COUNTER`   | Cumulative value that only increases                             | Total transactions           |
| `HISTOGRAM` | Snapshot histogram deriving `_bucket` / `_count` / `_sum` series | Transaction age distribution |
| `LABEL`     | Use as a Prometheus label                                        | Database name                |
| `DISCARD`   | Ignore this column                                               | Internal values              |

### Histogram Columns (HISTOGRAM)

`v1.4.0` introduces the `HISTOGRAM` column type: every row returned by the query counts
as one observation, aggregated per label group into a classic Prometheus histogram
snapshot, deriving three series families: `<name>_bucket` (with the `le` label and the
`+Inf` bucket), `<name>_count`, and `<name>_sum`:

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
  tags: [cluster]
  metrics:
    - datname: {usage: LABEL, description: "Database name"}
    - seconds:
        usage: HISTOGRAM
        bucket: [1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000]
        description: "Open transaction age snapshot in seconds"
```

Usage notes:

- This is a **snapshot** histogram: the whole distribution is rebuilt on every scrape,
  so bucket counts can go up or down — gauge-like semantics. `histogram_quantile()`
  works directly, but `rate()` / `increase()` over `_count` / `_sum` is meaningless
- SQL `NULL` observations are ignored by default; with an explicit `default`, they
  count as the default value
- `scale` is applied to the observation before bucket assignment; as with scalar
  columns, timestamp and boolean values are exempt from `scale`
- The [`pg_xact_age`](https://github.com/pgsty/pg_exporter/blob/main/config/0450-pg_xact_age.yml)
  collector in the default bundle serves as the reference implementation

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

Best practices:
- Set TTL less than your scrape interval
- Use longer TTL for expensive queries
- TTL of 0 disables caching

### Timeout Control

Prevent queries from running too long:

```yaml
timeout: 0.1   # 100ms default
timeout: 1.0   # 1 second for complex queries
timeout: -1    # Disable timeout (not recommended)
```

### Version Compatibility

Control which PostgreSQL versions can run this collector:

```yaml
min_version: 100000  # PostgreSQL 10.0+
max_version: 140000  # Below PostgreSQL 14.0
```

Version numbers follow PostgreSQL `server_version_num` rules:

- `100000` = 10.0
- `130200` = 13.2
- `160100` = 16.1
- `190000` = 19.0
- `90600` = 9.6, relevant when using the legacy config bundle

## Execution Model

Understanding the full path from a collector definition to emitted metrics helps answer "why is this metric missing":

1. **Planning** (on connection setup or hot reload): each collector branch is checked in turn — target type (PostgreSQL / PgBouncer), `min_version` / `max_version` gates, `tags` matching against server role and exporter tags, and the `skip` switch. Branches that fail any check are not installed on that target. `curl localhost:9630/explain` shows exactly the verdict of this step.
2. **Scraping** (on every `/metrics` request): for each installed collector — if the cache is still within `ttl`, the cached result is returned; otherwise `predicate_queries` run first (any false verdict skips this round and bumps `pg_exporter_query_scrape_predicate_skip_count`), then the main query executes under `timeout`, and results are converted to metrics and cached.
3. **Failure semantics**: a normal collector failure only affects itself (`pg_exporter_query_scrape_error_count` goes up, its metric group is absent this round); a failing collector marked `fatal: true` fails the whole server scrape.

## Tag System

Tags control when and where collectors execute:

### Built-in Tags

| Tag                   | Description                         |
|-----------------------|-------------------------------------|
| `cluster`             | Execute once per PostgreSQL cluster |
| `primary` / `master`  | Only on primary servers             |
| `standby` / `replica` | Only on replica servers             |
| `pgbouncer`           | Only for PgBouncer connections      |

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

The main query only executes if all predicates return `true`.

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

## Collector Organization

PG Exporter ships with pre-organized collectors:

| Range | Category      | Description                     |
|-------|---------------|---------------------------------|
| 0xx   | Documentation | Examples and documentation      |
| 1xx   | Basic         | Server info, settings, metadata |
| 2xx   | Replication   | Replication, slots, receivers   |
| 3xx   | Persistence   | I/O, checkpoints, WAL           |
| 4xx   | Activity      | Connections, locks, queries     |
| 5xx   | Progress      | Vacuum, index creation progress |
| 6xx   | Database      | Per-database statistics         |
| 7xx   | Objects       | Tables, indexes, functions      |
| 8xx   | Optional      | Expensive/optional metrics      |
| 9xx   | PgBouncer     | Connection pooler metrics       |
| 10xx+ | Extensions    | Extension-specific metrics      |
{.full-width}

## Real-World Examples

### Simple Gauge Collector

```yaml
pg_connections:
  desc: "Current database connections"
  query: |
    SELECT
      count(*) as total,
      count(*) FILTER (WHERE state = 'active') as active,
      count(*) FILTER (WHERE state = 'idle') as idle,
      count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
    FROM pg_stat_activity
    WHERE pid != pg_backend_pid()
  ttl: 1
  metrics:
    - total: {usage: GAUGE, description: "Total connections"}
    - active: {usage: GAUGE, description: "Active connections"}
    - idle: {usage: GAUGE, description: "Idle connections"}
    - idle_in_transaction: {usage: GAUGE, description: "Idle in transaction"}
```

### Counter with Labels

```yaml
pg_table_stats:
  desc: "Table statistics"
  query: |
    SELECT
      schemaname,
      tablename,
      n_tup_ins,
      n_tup_upd,
      n_tup_del,
      n_live_tup,
      n_dead_tup
    FROM pg_stat_user_tables
  ttl: 10
  metrics:
    - schemaname: {usage: LABEL}
    - tablename: {usage: LABEL}
    - n_tup_ins: {usage: COUNTER, description: "Tuples inserted"}
    - n_tup_upd: {usage: COUNTER, description: "Tuples updated"}
    - n_tup_del: {usage: COUNTER, description: "Tuples deleted"}
    - n_live_tup: {usage: GAUGE, description: "Live tuples"}
    - n_dead_tup: {usage: GAUGE, description: "Dead tuples"}
```

### Version-Specific Collector

```yaml
pg_wal_stats:
  desc: "WAL statistics (PG 14+)"
  min_version: 140000
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

```yaml
pg_stat_statements_metrics:
  desc: "Query performance statistics"
  tags: [extension:pg_stat_statements]
  query: |
    SELECT
      sum(calls) as total_calls,
      sum(total_exec_time) as total_time,
      sum(mean_exec_time * calls) / sum(calls) as mean_time
    FROM pg_stat_statements
  ttl: 60
  metrics:
    - total_calls: {usage: COUNTER}
    - total_time: {usage: COUNTER, scale: 0.001}
    - mean_time: {usage: GAUGE, scale: 0.001}
```

## Custom Collectors

### Creating Your Own Metrics

1. Create a new YAML file in your config directory:

```yaml
# /etc/pg_exporter/custom_metrics.yml
app_metrics:
  desc: "Application-specific metrics"
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

2. Test your collector:

```bash
pg_exporter --explain --config=/etc/pg_exporter/
```

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
      parent.relname as parent_table,
      count(*) as partition_count,
      sum(pg_relation_size(child.oid)) as total_size
    FROM pg_inherits
    JOIN pg_class parent ON parent.oid = pg_inherits.inhparent
    JOIN pg_class child ON child.oid = pg_inherits.inhrelid
    WHERE parent.relkind = 'p'
    GROUP BY parent.relname
  ttl: 300
  metrics:
    - parent_table: {usage: LABEL}
    - partition_count: {usage: GAUGE}
    - total_size: {usage: GAUGE}
```

## Performance Optimization

### Query Optimization Tips

1. **Use appropriate TTL values**:
    - Fast queries: 1-10 seconds
    - Medium queries: 10-60 seconds
    - Expensive queries: 300-3600 seconds

2. **Set realistic timeouts**:
    - Default: 100ms
    - Complex queries: 500ms-1s
    - Never disable timeout in production

3. **Use cluster-level tags**:
   ```yaml
   tags: [cluster]  # Run once per cluster, not per database
   ```

4. **Disable expensive collectors**:
   ```yaml
   pg_table_bloat:
     skip: true  # Disable if not needed
   ```

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
| High memory usage | Reduce result set size, use LIMIT                    |
| Permission errors | Verify query permissions for monitoring user         |

### Debug Logging

Enable debug logging to troubleshoot:

```bash
pg_exporter --log.level=debug
```
