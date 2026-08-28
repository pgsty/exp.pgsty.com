---
title: "Turning PostgreSQL CSV Logs into Durable Metrics"
linkTitle: "PostgreSQL Log Metrics"
date: "2026-08-24T12:17:38+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
authors: [Vonng]
description: "The product boundary, durable-state protocol, bounded metric contract, and failure semantics for PostgreSQL CSV log metrics in PG Exporter"
summary: "Implemented but unreleased. One default-off worker turns complete PostgreSQL CSV records into bounded durable counters and histograms, persisting cursor and aggregates before publishing an immutable snapshot."
categories: [design]
tags: [Design, PostgreSQL, Logging, Prometheus, Reliability]
---

> **Decision status:** Implemented in a development line; not present in `main`, a tag, or a published package as of 2026-08-28.<br>
> **Decision date:** 2026-08-24.<br>
> **Applies to:** the default-off PostgreSQL 14+ CSV log collector inside the Composite exporter.<br>
> **Supersedes:** the separate observability-product direction recorded in [The PostgreSQL Observability Product We Chose Not to Build](/design/observability-product-pivot/).<br>
> **Release boundary:** implementation and source-level tests exist; merge, release, package, Pigsty deployment, and production canary remain separate gates.

PostgreSQL logs contain operational facts that SQL snapshots cannot reconstruct: deadlocks, authentication failures, canceled autovacuum workers, checkpoint phases, temporary-file removals, client disconnects, and the duration of statements selected by logging policy. The design question was not whether those records were useful. It was how to expose a small reliable subset without turning PG Exporter into a log platform.

The final boundary is deliberately narrow:

> PG Exporter continuously reads one local PostgreSQL CSV log directory, persists a bounded aggregate state, and publishes low-cardinality counters and histograms on the existing `/metrics` endpoint. It does not store, search, or send raw logs.

## Product boundary {#product-boundary}

The collector belongs to the existing `pg_exporter` binary, package, service, target, and `/metrics` endpoint. It is enabled only by a non-empty log directory:

```bash
pg_exporter \
  --pg-log-dir=/var/log/postgresql \
  --pg-log-state-file=/var/lib/pg_exporter/pglog-state.json \
  --pg-log-poll-interval=1s
```

The environment equivalents are `PG_EXPORTER_PG_LOG_DIR`, `PG_EXPORTER_PG_LOG_STATE_FILE`, and `PG_EXPORTER_PG_LOG_POLL_INTERVAL`. The default directory is empty, the default state path is `/var/lib/pg_exporter/pglog-state.json`, and the default poll interval is one second.

When disabled, no worker, file scan, state lock, state file, log metric family, or extra scrape coordination exists. `--dry-run` and `--explain` do not start the worker.

The feature explicitly does not provide JSONLOG, stderr, syslog, journald, cloud log APIs, other component logs, log shipping, OTLP, Kafka, VictoriaLogs, Loki, full-text search, a TUI, session timelines, arbitrary regular expressions, a reset endpoint, or automatic root-cause analysis. PostgreSQL logging settings remain ordinary SQL/deployment configuration; there are no `pg_log_setting_*` metrics.

## Why CSV and why complete records {#csv-contract}

PostgreSQL 14 through 18 document the same 26 CSV columns. They include timestamp, user, database, process and session identity, per-session line number, severity, SQLSTATE, message fields, application, backend type, parallel leader PID, and query ID. PostgreSQL's sample import schema uses `(session_id, session_line_num)` as a primary key.

CSV is not one record per physical line. Query, detail, hint, and context fields may contain commas, quotes, carriage returns, and embedded newlines. A `bufio.Scanner`, `tail -F | regex`, or `strings.Split` implementation will eventually split one logical record into several false records.

The collector uses a complete CSV framing state machine and the standard CSV decoder. An unfinished record at the active file's end is retained as pending input; its offset is not committed until the complete logical record parses. A single record is bounded at 16 MiB. Malformed or oversized data enters a bounded resynchronization path and increments explicit parse and gap counters rather than silently advancing as if nothing happened.

The first release targets PostgreSQL 14+ because that gives one fixed 26-column schema. A repeated schema mismatch degrades the component instead of guessing a different format.

## Polling, file identity, and rotation {#file-semantics}

The worker periodically reconciles the directory instead of relying on `fsnotify`. Polling is easier to make portable and auditable across rename rotation, missed notifications, restarts, and directories that already contain several generations.

Each cursor records a stable file identity, generation, hashed path identity, byte offset, size, a small content fingerprint, EOF/disappearance state, and resynchronization state. The durable file does not retain the clear log path.

Rename rotation is followed by identity: the old file can be completed after its pathname changes while the new file begins at its own cursor. If a file becomes smaller than the committed offset, the collector treats it as truncation, resets that generation to offset zero, and increments both rotation and input-gap metrics. Copy-truncate can overwrite unread bytes before any reader observes them, so the design reports the unavoidable gap rather than promising impossible exactly-once delivery.

Missing unfinished files and fingerprint identity changes are also explicit gaps. Completed disappeared cursors become evictable tombstones. The state tracks at most 256 file identities; it will not evict active work merely to stay under the limit.

On first startup without state, existing files are baselined at their current EOF. This avoids treating an arbitrary retained history as new counters. The baseline increments `state_resets_total` and an input-gap reason so operators can see that metrics begin at a new epoch. Deliberate historical backfill is outside the first contract.

## The durable commit protocol {#durable-commit}

Counters and Histograms derived from log records must survive a PG Exporter restart. Advancing a cursor without its aggregates loses metrics; publishing aggregates without the matching cursor duplicates them after restart. The design commits them as one versioned state object.

One background cycle follows this order:

```text
scan and read complete records
    -> clone previous state
    -> update cursors, counters, histograms, and self-state
    -> validate monotonicity, labels, limits, and metric families
    -> write a 0600 temporary state file
    -> fsync temporary file
    -> atomic rename
    -> fsync parent directory where supported
    -> publish the matching immutable metric snapshot
```

The state file is capped at 4 MiB and must be a regular file with mode `0600`; symlinks and unsafe permissions are rejected. A non-blocking state lock prevents two processes from owning the same cursor. The directory identity stored in state must match the configured source.

The publication point matters. A crash before rename leaves the old state and old snapshot. A crash after rename but before the next scrape leaves the new durable state, which reconstructs the same families on restart. The request path reads only an atomic pointer; it never scans files, parses CSV, writes state, or calls `fsync`.

Each pass is bounded to 100,000 records or 64 MiB. If backlog remains, the worker immediately runs another pass instead of sleeping for the normal poll interval.

## Metrics and cardinality {#metric-contract}

The core families are:

```text
pg_log_records_total{severity}
pg_log_errors_total{severity,sqlstate_class}
pg_log_query_duration_seconds{kind}
pg_log_events_total{category,event}
```

The regular default surface also covers bounded exact SQLSTATE, checkpoint and restartpoint counts/durations/WAL activity, autovacuum outcomes and durations, lock waits, temporary-file counts and sizes, connections, and session durations.

Unlike the SQL [Snapshot Histogram](/design/snapshot-histograms/), log Histograms are durable cumulative observations. Their bucket, count, and sum state is persisted together with the cursor, so ordinary Prometheus counter-Histogram queries such as `rate()` apply until an explicit state reset creates a visible new epoch.

Labels are fixed enumerations. Query duration, for example, uses `statement`, `execute`, `parse`, `bind`, or `other`. Exact SQLSTATE is restricted to official codes, capped at 128 observed code series, with custom and unknown values folded into `other`. The complete log surface has a hard limit of 1,200 series.

Raw query, message, detail, hint, context, database, user, application, relation, query ID, client address, PID, session, transaction ID, and file path never enter labels or durable state. A record may contribute to several safe aggregates, but it can produce at most one primary classified event.

These decisions trade forensic detail for predictable monitoring. The exporter can alert that deadlocks or authentication failures increased; it cannot show the SQL text that caused them.

## Self-observability and trust {#self-observability}

Business metrics are insufficient without evidence that the reader is healthy. The collector adds:

```text
pg_exporter_log_bytes_read_total
pg_exporter_log_parse_errors_total{reason}
pg_exporter_log_files_watched
pg_exporter_log_last_record_timestamp_seconds
pg_exporter_log_state_persist_timestamp_seconds
pg_exporter_log_rotations_total{type}
pg_exporter_log_input_gaps_total{reason}
pg_exporter_log_state_resets_total
```

It also participates in `pg_exporter_component_*{component="postgres_log"}`. Input, permission, parser, state, limit, or family-conflict failures mark only the log component down. The last committed business snapshot remains available when safe, while `up`, last-success time, and error counters show that it is stale or incomplete.

`--disable-intro` removes exporter/component/log-reader self-metrics but retains `pg_log_*` business metrics, matching the existing distinction between exporter introspection and collected domain data.

## Logging policy changes metric meaning {#logging-policy}

The collector measures records PostgreSQL chose to emit. `pg_log_query_duration_seconds` is therefore a conditional distribution determined by `log_duration`, `log_min_duration_statement`, sampling, and protocol behavior. It must never be described as the distribution of every query unless PostgreSQL was configured to log every query duration.

Checkpoint, autovacuum, connection, disconnection, lock-wait, and temporary-file families are similarly present only when the corresponding server settings produce those messages. PG Exporter documents these prerequisites but does not duplicate settings as log-derived metrics.

PostgreSQL logs may contain sensitive statements and client data. The service account needs read access to the selected directory, but files should not be made world-readable. The collector stores only bounded aggregates and hashed source identity; it does not copy raw records to state.

## Alternatives rejected {#alternatives}

- Reading logs during `/metrics` was rejected because parse and persistence latency would enter the PostgreSQL scrape path.
- `fsnotify` was rejected as the correctness authority because notifications can be missed and do not replace reconciliation after restart.
- Processing all historical files on first start was rejected because retention policy would redefine counter origin unpredictably.
- At-least-once publication was rejected because duplicate alert counters are not an acceptable recovery strategy.
- Dynamic labels and user regular expressions were rejected because input data could control cardinality and durable schema.
- A new endpoint or binary was rejected because the feature is a bounded metric source, not a second product.

## Acceptance and remaining gates {#acceptance}

Source-level acceptance covers PostgreSQL 14, 16, and 18 fixtures; quoted commas, quotes, CRLF, multiline and partial records; rename rotation, truncation, restart restoration, state locks and permissions; crash points around state persistence; event-catalog fixtures; series budgets; family conflicts; disabled fast path; overlapping scrape behavior; shutdown; race tests; and package metadata.

Those tests establish an implementation candidate, not a public release. Before delivery, the exact merged commit must pass repository CI and package builds, then run under the final service user against a disposable PostgreSQL instance with real rotation and restart. Pigsty targets, dashboards, recording rules, alerts, package upgrades, and production canary results require separate evidence.

The Composite coordination contract is documented in [One Endpoint, Several Sources](/design/composite-exporter/). PostgreSQL remains the authority for the CSV schema and logging prerequisites: [PostgreSQL 14 logging](https://www.postgresql.org/docs/14/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) and [PostgreSQL 18 logging](https://www.postgresql.org/docs/18/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG).
