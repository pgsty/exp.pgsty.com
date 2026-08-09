---
title: "Bundled Collectors"
linkTitle: "Collectors"
description: "Inventory, prerequisites, and operating guidance for all 58 collector definition files shipped with PG Exporter"
weight: 100
icon: fa-solid fa-table-list
categories: [Reference]
---

PG Exporter v{{< param version >}} ships **58 collector definition files** under [`config/`](https://github.com/pgsty/pg_exporter/tree/main/config). They are merged in filename order into the default [`pg_exporter.yml`](https://github.com/pgsty/pg_exporter/blob/main/pg_exporter.yml) by `make conf`.

The filename prefix is an ordering convention, not a metric name. A file can define multiple version- or role-specific branches with the same public metric namespace. At startup, PG Exporter evaluates server facts and installs only the eligible branch; [`GET /explain`](/api/#get-explain) shows that plan for the connected target.

## Numbering Map

| Range | Area | Typical scope |
|:---|:---|:---|
| `0000` | Authoring reference | YAML schema and examples; not an installed collector |
| `0100` | Identity and settings | Server identity, metadata, configuration limits |
| `0200` | Replication | senders, receivers, slots, subscriptions, origins |
| `0300` | Instance internals | I/O, storage, checkpoints, recovery, SLRU, shared memory |
| `0400` | Workload | WAL, sessions, waits, transactions, locks, query statistics |
| `0500` | Progress | VACUUM, indexing, clustering, and backup progress |
| `0600` | Database and logical replication | database counters, conflicts, publication/subscription state |
| `0700` | Relations | tables, indexes, functions, sequences, partitions |
| `0800` | Expensive relation analysis | size and bloat collectors |
| `0900` | PgBouncer | lists, databases, statistics, pools |
| `1000+` | Optional integrations | wait sampling, TimescaleDB, Citus, heartbeat |
{.full-width}

## Complete Inventory

| File | Namespace | Scope and requirement |
|:---|:---|:---|
| [`0000-doc.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0000-doc.yml) | config reference | YAML schema and collector authoring guide; not installed |
| [`0110-pg.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0110-pg.yml) | `pg` | Basic server information, with primary and replica branches |
| [`0120-pg_meta.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0120-pg_meta.yml) | `pg_meta` | Cluster metadata; PG13+ includes `primary_conninfo` |
| [`0130-pg_setting.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0130-pg_setting.yml) | `pg_setting` | Shared settings and capacity limits |
| [`0210-pg_repl.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0210-pg_repl.yml) | `pg_repl` | Replication sender statistics |
| [`0220-pg_sync_standby.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0220-pg_sync_standby.yml) | `pg_sync_standby` | Synchronous standby status |
| [`0230-pg_downstream.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0230-pg_downstream.yml) | `pg_downstream` | Downstream replication client counts |
| [`0240-pg_slot.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0240-pg_slot.yml) | `pg_slot` | Replication slots; standby-aware on PG16+, PG19 invalidation reason support |
| [`0250-pg_recv.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0250-pg_recv.yml) | `pg_recv` | Replica WAL receiver; PG19 `connecting` status support |
| [`0260-pg_sub.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0260-pg_sub.yml) | `pg_sub` | Subscription statistics; PG19 sync-error and conflict counters |
| [`0270-pg_origin.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0270-pg_origin.yml) | `pg_origin` | Replication origins; disabled by default, may need extra privileges |
| [`0300-pg_io.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0300-pg_io.yml) | `pg_io` | `pg_stat_io` on PG16+, with a PG18+ branch |
| [`0310-pg_size.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0310-pg_size.yml) | `pg_size` | Database, WAL, and log sizes |
| [`0320-pg_archiver.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0320-pg_archiver.yml) | `pg_archiver` | Archiver process statistics |
| [`0330-pg_bgwriter.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0330-pg_bgwriter.yml) | `pg_bgwriter` | Background writer statistics, with a PG17+ branch |
| [`0331-pg_checkpointer.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0331-pg_checkpointer.yml) | `pg_checkpointer` | Checkpointer statistics; PG18+ completion and SLRU counters |
| [`0340-pg_ssl.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0340-pg_ssl.yml) | `pg_ssl` | SSL client connection counts |
| [`0350-pg_checkpoint.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0350-pg_checkpoint.yml) | `pg_checkpoint` | Checkpoint control information |
| [`0355-pg_timeline.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0355-pg_timeline.yml) | `pg_timeline` | Current timeline ID on primary or replica |
| [`0360-pg_recovery.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0360-pg_recovery.yml) | `pg_recovery`, `pg_recovery_prefetch` | Replica recovery and recovery-prefetch statistics |
| [`0370-pg_recovery_state.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0370-pg_recovery_state.yml) | `pg_recovery_state` | PG19 replica recovery state from `pg_stat_recovery` |
| [`0380-pg_slru.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0380-pg_slru.yml) | `pg_slru` | SLRU cache statistics on PG13+ |
| [`0390-pg_shmem.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0390-pg_shmem.yml) | `pg_shmem` | Shared memory allocation; disabled by default, requires `schema:monitor` |
| [`0400-pg_wal.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0400-pg_wal.yml) | `pg_wal` | WAL statistics on PG14+; PG19 adds full-page-image byte counters |
| [`0410-pg_activity.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0410-pg_activity.yml) | `pg_activity` | Backend counts by database and state |
| [`0420-pg_wait.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0420-pg_wait.yml) | `pg_wait` | Backend waits by wait-event type |
| [`0430-pg_backend.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0430-pg_backend.yml) | `pg_backend` | Backend counts grouped by `backend_type` |
| [`0440-pg_xact.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0440-pg_xact.yml) | `pg_xact` | Transaction snapshot boundaries and active transaction count |
| [`0450-pg_xact_age.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0450-pg_xact_age.yml) | `pg_xact_age` | PG10+ per-database open and idle transaction age histograms |
| [`0460-pg_lock.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0460-pg_lock.yml) | `pg_lock` | Lock distribution by database and mode |
| [`0470-pg_lock_stat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0470-pg_lock_stat.yml) | `pg_lock_stat` | PG19 cluster-wide lock wait and fast-path overflow counters |
| [`0480-pg_query.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0480-pg_query.yml) | `pg_query` | Query statistics; requires `extension:pg_stat_statements` |
| [`0510-pg_vacuuming.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0510-pg_vacuuming.yml) | `pg_vacuuming` | Primary-only VACUUM progress; PG18+ includes `delay_time` |
| [`0520-pg_indexing.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0520-pg_indexing.yml) | `pg_indexing` | Primary-only `CREATE INDEX` progress |
| [`0530-pg_clustering.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0530-pg_clustering.yml) | `pg_clustering` | Primary-only `CLUSTER` and `VACUUM FULL` progress |
| [`0540-pg_backup.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0540-pg_backup.yml) | `pg_backup` | Base backup progress on PG13+ |
| [`0610-pg_db.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0610-pg_db.yml) | `pg_db` | Per-database statistics; PG18+ parallel-worker counters |
| [`0620-pg_db_confl.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0620-pg_db_confl.yml) | `pg_db_confl` | Replica database conflict counters |
| [`0640-pg_pubrel.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0640-pg_pubrel.yml) | `pg_pubrel` | Publication and publication-relation counts |
| [`0650-pg_subrel.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0650-pg_subrel.yml) | `pg_subrel` | Subscription relation counts grouped by state |
| [`0660-pg_vacuum_score.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0660-pg_vacuum_score.yml) | `pg_vacuum_score` | PG19 autovacuum score summary from `pg_stat_autovacuum_scores` |
| [`0700-pg_table.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0700-pg_table.yml) | `pg_table` | Per-table statistics; PG18+ maintenance-time and new-page counters |
| [`0710-pg_index.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0710-pg_index.yml) | `pg_index` | Per-index statistics |
| [`0720-pg_func.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0720-pg_func.yml) | `pg_func` | Function execution statistics |
| [`0730-pg_seq.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0730-pg_seq.yml) | `pg_seq` | Sequence metrics |
| [`0740-pg_relkind.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0740-pg_relkind.yml) | `pg_relkind` | Relation counts by kind |
| [`0750-pg_defpart.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0750-pg_defpart.yml) | `pg_defpart` | Default partition tuple counts |
| [`0810-pg_table_size.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0810-pg_table_size.yml) | `pg_table_size` | Per-table sizes; can be slow on large schemas |
| [`0820-pg_table_bloat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0820-pg_table_bloat.yml) | `pg_table_bloat` | Disabled by default; requires auxiliary view `pg_table_bloat` |
| [`0830-pg_index_bloat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0830-pg_index_bloat.yml) | `pg_index_bloat` | Disabled by default; requires auxiliary view `pg_index_bloat` |
| [`0910-pgbouncer_list.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0910-pgbouncer_list.yml) | `pgbouncer_list` | PgBouncer list metrics from the admin database |
| [`0920-pgbouncer_database.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0920-pgbouncer_database.yml) | `pgbouncer_database` | PgBouncer database metrics with version-specific branches |
| [`0930-pgbouncer_stat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0930-pgbouncer_stat.yml) | `pgbouncer_stat` | PgBouncer per-database statistics with version-specific branches |
| [`0940-pgbouncer_pool.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0940-pgbouncer_pool.yml) | `pgbouncer_pool` | PgBouncer pool metrics with version-specific branches |
| [`1000-pg_wait_event.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/1000-pg_wait_event.yml) | `pg_wait_event`, `pg_wait_event_1s` | Wait sampling; requires `extension:pg_wait_sampling` |
| [`1800-pg_tsdb_hypertable.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/1800-pg_tsdb_hypertable.yml) | `pg_tsdb_hypertable` | Disabled by default; requires TimescaleDB and its information schema |
| [`1900-pg_citus.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/1900-pg_citus.yml) | `pg_citus_node` | Citus worker/coordinator inventory; requires `extension:citus` |
| [`2000-pg_heartbeat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/2000-pg_heartbeat.yml) | `pg_heartbeat` | Disabled by default; requires the `monitor` heartbeat table in `postgres` |
{.full-width}

## Plan Before Enabling

Do not treat all 58 files as 58 unconditional queries. The planner selects branches using PostgreSQL or PgBouncer version, recovery role, target database, extensions, schemas, username, and predicate results. Inspect the real plan before tuning:

```bash
curl -fsS http://127.0.0.1:9630/explain
curl -fsS http://127.0.0.1:9630/explain | jq '.[] | {name, status, reason}'
```

Disabled collectors deserve an explicit review. `pg_origin`, `pg_shmem`, both bloat collectors, the TimescaleDB collector, and `pg_heartbeat` are intentionally not enabled in the generic plan because they need privileges, helper objects, a specific extension, or a deliberate write/read workflow.

## Cardinality and Cost

Per-relation and per-query collectors are the main cardinality drivers. Review these before enabling them on a large estate:

- `pg_table`, `pg_index`, `pg_func`, and `pg_seq` emit one or more series per object.
- `pg_query` grows with the normalized statements retained by `pg_stat_statements`.
- `pg_table_size`, `pg_table_bloat`, and `pg_index_bloat` can be expensive on catalogs with many relations.
- Wait-event sampling uses an extension and can emit dimensions that vary with workload.

Use collector `ttl` to cache expensive results, set a realistic per-collector `timeout`, and scrape at an interval that exceeds the slowest expected collector. Compare `/metrics` duration and series count before and after a change; never infer safety from config validation alone.

## Customize Safely

Keep local collector overrides in a separate directory rather than editing the generated monolith. Copy the smallest relevant file, give every top-level branch a globally unique name, preserve non-overlapping version ranges, and validate the result with:

```bash
pg_exporter --config=/path/to/collectors --dry-run
PG_EXPORTER_CONFIG=/path/to/collectors pg_exporter
curl -fsS http://127.0.0.1:9630/explain
curl -fsS http://127.0.0.1:9630/metrics >/dev/null
```

The complete collector schema, query-to-metric mapping, tags, predicates, cache behavior, timeout semantics, and histogram rules are documented in [Collector Configuration](/config/).
