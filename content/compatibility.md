---
title: "Compatibility"
linkTitle: "Compatibility"
description: "Supported PostgreSQL and PgBouncer versions, release artifacts, architectures, and deployment constraints"
weight: 40
icon: fa-solid fa-layer-group
categories: [Reference]
---

Choose an artifact for the exporter host and a collector configuration for the database version. Then install any views or extensions required by the collectors you enable. This page describes the default configuration shipped with v{{< param version >}} and the separately maintained legacy bundle.

## Database Targets {#database-targets}

| Target | Status | Configuration |
|:---|:---|:---|
| PostgreSQL 10-18 | Default support | `pg_exporter.yml` / `config/` |
| PostgreSQL 19 | Version-specific branches included | Default config; check queries against your server build |
| PostgreSQL 9.1-9.6 | Historical legacy support | Current `legacy/pg_exporter.yml` / `legacy/config/` on main |
| PostgreSQL 9.0 and older | Unsupported | — |
| PgBouncer 1.8+ | Version-specific collectors | `0910`-`0940` collector files; connect to the admin database |
{.full-width .wide .expand}

PostgreSQL 19 branches cover recovery, locks, autovacuum scores, WAL, subscriptions, receivers, and replication slots. Version selection uses the server version number; check `/stat` after the first scrape to find queries that need adjustment for your server build.

The bundled PgBouncer collectors require 1.8 or later. That version changed the `SHOW STATS` fields used by these queries. The latest configured branches have no upper version bound. When you upgrade PgBouncer, check collector results against the [upstream changelog](https://www.pgbouncer.org/changelog.html).

## Release Validation {#release-validation}

The v1.6.0 release baseline passed primary collection as a non-superuser on PostgreSQL 9.2–9.6 with the legacy bundle, PostgreSQL 10–18 and 19 RC1 with the default bundle, and PgBouncer 1.26.1. PostgreSQL 10–13 used the documented subscription OID grant. Physical standby promotion, reconnect recovery, concurrent scrape/health/reload, HTTPS authentication, package installation, and upgrades from 1.5.0 were also tested. PostgreSQL 19 evidence refers to RC1. A follow-up verified PostgreSQL 9.1–9.6 with the legacy configuration at `282e19d` (included in the v1.6.1 source tag), covering tables with and without TOAST; see [installation](/install/#compatibility).

The v1.6.1 maintenance release passed the full race and Go 1.21 HTTP-mux test suites, module and generated-config gates, six-target cross-builds, RPM/DEB package installation and checksum checks (Debian 12 and Rocky Linux 9), published multi-arch Docker CA/TLS/payload and live streaming-primary verification, and non-superuser (`monitor`) live acceptance across PostgreSQL 9.1–9.6 (`legacy/pg_exporter.yml`), PostgreSQL 10–18 and 19 RC1 primaries (`pg_exporter.yml`), PostgreSQL 18 and 19 RC1 physical streaming standbys, and PgBouncer 1.26.1 with zero query errors. Windows, Linux ppc64le, and Intel macOS artifacts received build/checksum checks rather than runtime acceptance. These checks do not establish coverage of every extension, server build, or production workload.

## Metric and Dashboard Compatibility {#metric-compatibility}

An exporter upgrade and a PostgreSQL major-version upgrade can change different parts of the metric contract. The comparisons below use the bundled SQL collectors at tags [`v1.4.1`](https://github.com/pgsty/pg_exporter/tree/v1.4.1/config), [`v1.5.0`](https://github.com/pgsty/pg_exporter/tree/v1.5.0/config), [`v1.6.0`](https://github.com/pgsty/pg_exporter/tree/v1.6.0/config), and [`v1.6.1`](https://github.com/pgsty/pg_exporter/tree/v1.6.1/config), including each column's `rename` setting. They describe exported metric names, not just PostgreSQL view columns or YAML filenames. Custom collectors and application-specific alert rules need their own review.

### Exporter v1.6.0 → v1.6.1 {#exporter-161-metrics}

No built-in SQL metric names, label keys, types, buckets, HTTP routes, or CLI flags change. The default bundle retains 58 YAML files, 96 branches, 59 namespaces, and 460 distinct metric definitions. The following SQL value and runtime edge-case fixes ship in v1.6.1:

| Surface | Change | Upgrade action |
|:---|:---|:---|
| `pg_table_age`, scan totals, and row estimates | All four branches report zero for `relfrozenxid = 0`; nullable terms no longer erase valid scan/tuple totals; nullable row estimates default to zero | Deploy the new YAML; review partitioned-parent freeze-age alerts and corrected indexless-table values |
| `pg_table_size_*` | Excludes `pg_temp*` and `pg_toast*` schemas as well as the catalog/information schemas | Deploy the new YAML to avoid querying another session's temporary tables |
| `pg_activity_max_*_duration` | Negative state, transaction, and session durations clamp to zero | Deploy the new YAML |
| `pg_tsdb_hypertable_*` | Quotes schema and hypertable names correctly | Deploy the new YAML if enabling this optional collector |
| Duplicate scalar rows | Repeated label tuples fail that collector; non-fatal failures allow other collectors to continue. Histogram-only queries still aggregate repeated tuples | Ensure scalar queries return one row per label tuple; fix cross-collector collisions separately |
| Numeric options and self-metrics | `scale` / `default` must be finite; invalid namespaces fail startup; build-info fields cannot be overwritten | Review custom YAML and constant labels; upgrade the binary |
| Child-database pools | Removed or replaced targets close old pools safely; reload reuses pools and invalidates plans | Upgrade the binary; reload is not a connection-pool reset |
| systemd reload | Packaged unit gains `ExecReload` | Refresh the unit with `daemon-reload`; restart for binary changes, reload for YAML-only changes |
{.full-width .wide .expand}

### Exporter v1.5.0 → v1.6.0 {#exporter-160-metrics}

No built-in SQL metric names, label keys, types, or units change on the same PostgreSQL version. The bundle still has 460 distinct metric definitions. The following behavior and label values do change:

| Surface | Change | Upgrade action |
|:---|:---|:---|
| `pg_vacuuming_*`, `pg_indexing_*`, `pg_clustering_*` | Foreign-database user relations use numeric OIDs in `relname`; connected-database and system-catalog names still resolve | Deploy the new YAML; retain `datname` and `pid` in dashboards and expect new label values |
| `/up` and role routes | Only health probes update HTTP state after initialization | A reachable target can return 200 even when a fatal collector makes `pg_up 0`; choose the signal appropriate to the alert |
| Scrape error counters | Interrupted passes do not add target errors | Use query-level errors and logs for individual query failures; see [API](/api/) |
| `/metrics` overlap | Two admitted requests; cancelable waiting; excess or expired collection returns 503 | Keep scrapers within the admission limit and check their time budgets |
| PgBouncer pool | Maximum connections increase from one to two | Allow one collection connection and one probe connection |
{.full-width .wide .expand}

The historical v1.6.0, v1.5.0, and PostgreSQL-version migrations still apply when upgrading from older versions. v1.6.1 does not add the experimental `snort` components.

### Exporter v1.4.1 → v1.5.0 {#exporter-150-metrics}

With the same PostgreSQL version, **no bundled SQL metric names are added, removed, or renamed**, and metric types and units remain unchanged. The following changes still require dashboard and alert review:

| Metric | Change in the v1.5.0 configuration | Migration action |
|:---|:---|:---|
| `pg_sub_*` | Every sample adds the owning database's `datname` label; `pg_sub_id` remains a Gauge. | Preserve `datname` and `subname`, plus target identity, in joins and per-subscription aggregations. A join using only `subname` can become ambiguous across databases. New label sets create new series and can restart an alert's pending period. |
| `pg_recv_state` | Keeps `streaming=0`, `stopping=4`, `connecting=5` (PG19+), and unknown/NULL `=-1`; adds `starting=6`, `waiting=7`, `restarting=8`, `stopped=9`. These four states previously fell through to `-1`. | Update Grafana value mappings and rules that only recognize `-1` or the old 0–5 range. Codes 1–3 are reserved; `startup`, `catchup`, and `backup` were sender states mistakenly listed for this receiver metric. No receiver row still means no sample. |
| `pg_subrel_count`, `pg_pubrel_count` | HELP text clarifies existing table/sequence counting; this release does not change their SQL, labels, or values. | Do not compare these counts as if they represented the same set of objects. See the PG19 behavior below. |
{.full-width .wide .expand}

These corrections require deploying the updated YAML as well as the binary. On PG10–13, the subscription collector also needs the [subscription OID grant](/collectors/#subscription-identity-and-receiver-states); otherwise its metrics disappear because the query fails. See the [replication design record](/design/replication-collector-contracts/) for the compatibility decisions.

### PostgreSQL 18 → 19 with the v1.5.0 configuration {#postgresql-19-metrics}

**No metric names from the PG18 branches are removed or renamed by switching to the PG19 branches.** PostgreSQL 19 collector support first shipped in [Exporter v1.3.0](/release/v1.3.0/); the behavior below is inherited by v1.5.0. It is separate from the label and receiver corrections above. PostgreSQL acceptance evidence is for 19 RC1.

| Metric or family | PG19 behavior | Dashboard / alert impact |
|:---|:---|:---|
| `pg_sub_sync_error_count` | Retained as `sync_table_error_count + sync_seq_error_count`; on PG15–18 it counts initial table synchronization errors only. | Existing all-sync-error alerts keep a metric to query, but now include sequence synchronization errors. Review thresholds; this is a broader meaning under the same name. |
| `pg_sub_sync_table_error_count`, `pg_sub_sync_seq_error_count` | Separate new Counters for table and sequence synchronization errors. | Use the table counter to retain table-only semantics on PG19. Do not add these counters to `pg_sub_sync_error_count`, which already includes both. |
| `pg_sub_confl_*`, `pg_sub_reset_time`, `pg_sub_has_worker` | Adds eight conflict Counters, a statistics-reset timestamp Gauge, and a leader-apply-worker presence Gauge. The PG19 query starts from subscription statistics and keeps a subscription row even without an apply worker. | Use `pg_sub_has_worker == 0` for an expected-running subscription on PG19; the continued presence of `pg_sub_id` does not prove that a worker is running. Account for intentionally disabled subscriptions. |
| `pg_subrel_count` | Counts both tables and sequences, grouped by `datname`, `subname`, and `state`. Sequences use `i` or `r`; tables use `i`, `d`, `f`, `s`, or `r`. | A table-only panel can now include sequences. There is no relation-kind label to separate them. `pg_pubrel_count` still counts tables only and emits no series for an empty or sequence-only publication. |
| `pg_wal_fpi_bytes` | New Counter for full-page-image WAL bytes. | Additive. Existing `pg_wal_bytes` and `pg_wal_fpi` retain their names and meanings; the new metric is not a replacement for either. |
| `pg_lock_stat_waits`, `pg_lock_stat_wait_time`, `pg_lock_stat_fastpath_exceeded` | New Counters by `locktype`; wait time is exported in seconds. Wait statistics count waits longer than `deadlock_timeout`. | These complement the current lock distribution in `pg_lock_count`; they do not replace it or measure every short lock wait. |
| `pg_recovery_state_*` | Nine new recovery-state metrics, selected only on replicas. | Additive to `pg_recovery_*`; absence on a primary is expected. Review the metric's type before applying `rate()`. |
| `pg_vacuum_score_*` | Eleven new Gauges summarizing autovacuum scores and candidate counts per database, selected only on primaries. | Additive; absence on replicas or older servers is expected. These are current scores/counts, not cumulative event Counters. |
{.full-width .wide .expand}

Exact definitions are in the tagged [subscription](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0260-pg_sub.yml), [subscription relation](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0650-pg_subrel.yml), [WAL](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0400-pg_wal.yml), [lock](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0470-pg_lock_stat.yml), [recovery](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0370-pg_recovery_state.yml), and [autovacuum](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0660-pg_vacuum_score.yml) collectors.

For a mixed PG15–19 fleet using the v1.5.0 configuration, this expression preserves **table-only** synchronization-error rates. The left side takes precedence where the PG19 metric exists; labels and target selectors must agree:

```promql
rate(pg_sub_sync_table_error_count[5m])
or
rate(pg_sub_sync_error_count[5m])
```

### Upgrading from PG17 or earlier {#older-postgresql-metrics}

An upgrade straight to PG19 also crosses earlier PostgreSQL metric boundaries. The following names are absent on PG19 with the v1.5.0 bundle; their disappearance is **not new in Exporter v1.5.0 or PostgreSQL 19**.

| Old metric | First absent on | Replacement or action |
|:---|:---|:---|
| `pg_bgwriter_checkpoints_timed` | PG17 | `pg_checkpointer_timed` |
| `pg_bgwriter_checkpoints_req` | PG17 | `pg_checkpointer_req` |
| `pg_bgwriter_checkpoint_write_time` | PG17 | `pg_checkpointer_write_time` (seconds) |
| `pg_bgwriter_checkpoint_sync_time` | PG17 | `pg_checkpointer_sync_time` (seconds) |
| `pg_bgwriter_buffers_checkpoint` | PG17 | `pg_checkpointer_buffers_written` |
| `pg_bgwriter_buffers_backend`, `pg_bgwriter_buffers_backend_fsync` | PG17 | Review `pg_io_writes` / `pg_io_fsyncs` with the intended backend `type`, `object`, and `context`. These are not direct renames: I/O operations and buffer counts need not have identical scope or units. |
| `pg_wal_write` | PG18 | `pg_io_writes{object="wal"}` |
| `pg_wal_sync` | PG18 | `pg_io_fsyncs{object="wal"}` |
| `pg_wal_write_time` | PG18 | `pg_io_write_time{object="wal"}` (seconds) |
| `pg_wal_sync_time` | PG18 | `pg_io_fsync_time{object="wal"}` (seconds) |
{.full-width .wide .expand}

The `pg_checkpointer_*` names above are already provided by the v1.5.0 configuration on PG10–16, using aliases for the old SQL columns. Prefer those names for a mixed-version dashboard. PG18+ also exposes `pg_checkpointer_done` for completed checkpoints; `timed` and `req` count scheduled/requested checkpoints and should not be treated as a completed-work total. Checkpointer statistics on PG17+ include restartpoint activity where documented.

WAL I/O moves to a view with `type`, `object`, and `context` dimensions, so replacing a name alone is insufficient. For example, a per-target WAL write rate on PG18+ is:

```promql
sum by (job, instance) (rate(pg_io_writes{object="wal"}[5m]))
```

Keep any additional cluster/target labels required by your setup, review the chosen backend scope, and check timing settings before comparing historical values. PG18+ also adds `pg_io_read_bytes`, `pg_io_write_bytes`, and `pg_io_extend_bytes`; use these for byte throughput rather than assuming a fixed byte count per operation. See the tagged [I/O](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0300-pg_io.yml), [background-writer](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0330-pg_bgwriter.yml), and [checkpointer](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0331-pg_checkpointer.yml) definitions and [PostgreSQL 18 migration notes](https://www.postgresql.org/docs/18/release-18.html).

### Detect missing metrics before alerts go silent {#missing-metric-alerts}

A Prometheus alert whose expression returns an empty vector has no active alert instances. HTTP 200, Prometheus `up == 1`, or `pg_up == 1` does not establish that every collector or alert expression still works. See [Prometheus alert evaluation](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/).

1. Merge and deploy the matching YAML, preserving local customizations. On a representative target of each version and role, scrape `/metrics`, inspect `/explain` and `/stat`, and check `pg_exporter_query_scrape_error_count` and the logs for collector failures.
2. Evaluate the actual dashboard, recording-rule, and alert expressions. Check names, label joins, units, state mappings, and returned series; wait for enough samples to fill `rate()` windows. An empty result is not a healthy zero.
3. Test alert rules with both expected data and missing-series input (`promtool check rules` checks syntax; `promtool test rules` can check behavior). A successful exporter test does not validate downstream dashboards.
4. Add per-target missing-metric checks only where that metric is expected for the server version, role, and configured objects. Do not hide missing input with a blanket `or vector(0)`.

For example, if `job="pg19"` contains only PG19 targets expected to expose the bundled WAL collector, this rule detects a missing `pg_wal_bytes` on each otherwise healthy target:

```yaml
groups:
  - name: pg-exporter-compatibility
    rules:
      - alert: PgWalMetricMissing
        expr: (pg_up{job="pg19"} == 1) unless on (job, instance) pg_wal_bytes{job="pg19"}
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Expected WAL metric is missing from a healthy PostgreSQL target"
```

Adapt the selector and matching labels to your target identity; monitor `up` and `pg_up` failures separately. For a known individual target, [`absent_over_time()`](https://prometheus.io/docs/prometheus/latest/querying/functions/#absent_over_time) is another option. A fleet-wide `absent(metric)` alone cannot detect one missing target while others still emit the metric. Likewise, `pg_recv_state != 0` cannot detect a receiver row that has disappeared; streaming-standby monitoring needs a separate expected-receiver presence check.

## v{{< param version >}} Release Artifacts {#release-artifacts}

| Artifact | Operating system | Architectures |
|:---|:---|:---|
| Tarball | Linux | amd64, arm64, ppc64le |
| Tarball | macOS | amd64, arm64 |
| Tarball | Windows | amd64 |
| RPM | RHEL-compatible Linux | x86_64, aarch64, ppc64le |
| DEB | Debian/Ubuntu-compatible Linux | amd64, arm64, ppc64le |
| Docker image | Linux container | amd64, arm64 |
{.full-width .wide .expand}

Release archives include the binary, merged default config, license, default environment file, and systemd unit. PostgreSQL 9.1–9.6 configuration is historical legacy support maintained separately on `main` under `legacy/` rather than bundled in binary archives or guaranteed by older source tags; see [installation](/install/#compatibility). macOS and Windows artifacts are useful for development and remote targets; the packaged service integration is Linux-specific.

> [!NOTE] RPM name since v1.4.1
> The official RPM package and artifact prefix is `pg-exporter`. It declares `Provides` and `Obsoletes` for the former `pg_exporter` name, so direct upgrades remain possible. The executable and configuration names remain `pg_exporter` and `/etc/pg_exporter.yml`.

## Container Constraints {#container-constraints}

The `scratch` image includes the system CA bundle and license, but no shell. Publicly trusted certificates can use the bundled roots; mount your private CA and set `sslrootcert` when using a private PKI with `sslmode=verify-ca` or `verify-full`.

## Collector-Level Requirements {#collector-level-requirements}

Collector selection also depends on the target database:

- `primary` / `replica` tags restrict execution by recovery role.
- `dbname:`, `extension:`, `schema:`, and `username:` tags require matching facts.
- Predicate queries can perform additional runtime checks.
- Disabled-by-default collectors (`skip: true`) must be intentionally enabled.
- Auxiliary-view collectors such as table/index bloat require their views and privileges.

Scrape `/metrics` once, then use [`/explain`](/api/#get-explain) to inspect the current plan and `/stat` to check query results. [Bundled Collectors](/collectors/) lists the prerequisites for each file.
