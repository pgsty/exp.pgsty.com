---
title: "Turning PostgreSQL CSV Logs into Durable Metrics"
linkTitle: "PostgreSQL Log Metrics"
date: "2026-08-24T12:17:38+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "Read complete CSV records, persist cursors and aggregates, and publish bounded PostgreSQL log metrics"
summary: "Implemented but unreleased. A default-off worker persists CSV cursors and aggregates before publishing cumulative log metrics."
categories: [design]
tags: [Design, PostgreSQL, Logging, Prometheus, Reliability]
---

PostgreSQL logs record events that SQL snapshots can miss: deadlocks, authentication failures, canceled autovacuum workers, checkpoints, temporary-file removals, and client disconnects. They can also report statement duration, according to the server's logging policy.

> **Status:** Implemented but unreleased.<br>
> **Decision date:** 2026-08-24.<br>
> **Last verified:** 2026-11-09.<br>
> **Scope:** Default-off PostgreSQL 14+ CSV log collector at source commit `c0ba58a` on the `snort` development branch; absent from stable `v1.6.0`.<br>
> **Replaces:** The [separate observability-product proposal](/design/observability-product-pivot/).<br>
> **Delivery:** Local tests passed. Not merged into `main` or tagged; packages, deployment, and production operation remain unverified.

This collector reads one local CSV log directory. It saves bounded aggregate state and exposes Counters and Histograms on `/metrics`. Raw logs remain in PostgreSQL's log files.

## Scope and activation {#product-boundary}

The collector runs in the existing PG Exporter process. A non-empty log directory enables it:

```bash
pg_exporter \
  --pg-log-dir=/var/log/postgresql \
  --pg-log-state-file=/var/lib/pg_exporter/pglog-state.json \
  --pg-log-poll-interval=1s
```

The corresponding environment variables are `PG_EXPORTER_PG_LOG_DIR`, `PG_EXPORTER_PG_LOG_STATE_FILE`, and `PG_EXPORTER_PG_LOG_POLL_INTERVAL`. Defaults are an empty directory, the state path shown above, and a one-second poll interval.

When disabled, the collector creates no worker, state lock, state file, or log metrics. It adds no file scans or scrape coordination. `--dry-run` and `--explain` do not start the worker.

The scope is local PostgreSQL CSV logs and aggregate metrics. Other log formats, log shipping, search interfaces, session timelines, arbitrary regular expressions, and automatic root-cause analysis are excluded. PostgreSQL logging settings remain server configuration; the collector does not create `pg_log_setting_*` metrics.

## Read complete CSV records {#csv-contract}

PostgreSQL 14 through 18 document the same 26-column CSV layout. It includes timestamps, process and session identifiers, severity, SQLSTATE, messages, application, backend type, parallel leader PID, and query ID.

Fields can contain commas, quotes, carriage returns, and newlines. The reader therefore frames complete CSV records before decoding them. A physical-line scanner cannot handle this format correctly.

An unfinished record at the end of a file stays pending. Its offset is committed only after the record is complete. Records have a 16 MiB limit. Malformed or oversized input triggers bounded resynchronization and increments parse-error and input-gap counters. Repeated schema mismatches keep the component down until valid input resumes.

## File identity and rotation {#file-semantics}

The worker polls and reconciles the directory. File notifications alone cannot recover missed events or reconstruct state after restart.

Each cursor holds a file identity, generation, hashed path, byte offset, size, content fingerprint, and reader status. The state file does not contain clear-text log paths.

Rename rotation follows file identity: the reader can finish the renamed file and start a cursor for the new one. A size below the committed offset means truncation. The reader starts a new generation at offset zero and records a rotation and an input gap. Copy-truncate can discard unread bytes before polling detects the change; those bytes cannot be recovered by this collector.

A missing unfinished file or changed fingerprint also records a gap. Completed, disappeared cursors can be removed. State tracks at most 256 file identities and retains cursors that still have unread work.

On first startup without state, the reader begins at the current end of every existing file. It increments the state-reset and input-gap counters to mark this new starting point. Historical backfill is outside this design.

## Commit state before metrics {#durable-commit}

Log Counters and Histograms must survive an exporter restart. Cursor offsets and aggregates are committed together: advancing one without the other would lose or duplicate observations.

A background cycle prepares a candidate state and then:

```text
read complete records and update candidate state
    -> validate counters, histograms, labels, and limits
    -> construct and validate metric families
    -> write a 0600 temporary state file
    -> fsync the file
    -> atomically rename it to the state path
    -> fsync the parent directory where supported
    -> publish the matching immutable metric snapshot
```

The state file is limited to 4 MiB. On Unix, it must be a regular file with mode `0600`; symlinks and unsafe permissions are rejected. A non-blocking state lock prevents two processes from using the same state. The saved directory identity must match the configured source.

A crash before rename leaves the previous committed state. A crash after rename allows restart to recover the new state and reconstruct its metrics. `/metrics` only reads the published snapshot; it performs no file scan, CSV parsing, or state write.

A pass processes at most 100,000 records or 64 MiB. If input remains, the next pass starts immediately.

## Metrics and series limits {#metric-contract}

Core families are:

```text
pg_log_records_total{severity}
pg_log_errors_total{severity,sqlstate_class}
pg_log_query_duration_seconds{kind}
pg_log_events_total{category,event}
```

Additional metrics cover exact SQLSTATE codes, checkpoints and restartpoints, autovacuum, lock waits, temporary files, connections, and session duration.

Log Histograms are cumulative observations persisted with the cursor. Use ordinary counter-Histogram queries such as `rate()`. An explicit state reset begins a new counter epoch. This differs from SQL [snapshot Histograms](/design/snapshot-histograms/), which describe the current population and use Gauge series.

Labels use fixed values. Query duration uses five `kind` values: `statement`, `execute`, `parse`, `bind`, and `other`. Exact SQLSTATE metrics admit official codes up to 128 observed code series; custom and unknown codes use `other`. The total output has a 1,200-series limit.

Raw SQL, messages, database and user names, application names, relations, query IDs, addresses, process and session IDs, transaction IDs, and file paths are excluded from labels and saved state. One record can update several aggregates but produces at most one primary classified event. The metrics identify an increase in deadlocks, for example, without retaining the SQL text.

## Reader health {#self-observability}

The reader exposes:

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

It also uses `pg_exporter_component_*{component="postgres_log"}`. Input, permission, parse, state, limit, or family-conflict errors mark only this component down. The last committed snapshot remains available. Use health, last-success time, and gap counters to assess its freshness and completeness.

`--disable-intro` removes exporter, component, and reader self-metrics. It keeps the `pg_log_*` business metrics.

## Logging policy determines coverage {#logging-policy}

Metrics cover the records PostgreSQL emits. Query-duration distributions depend on `log_duration`, `log_min_duration_statement`, sampling, and protocol behavior. For example, a slow-statement threshold produces a distribution of logged slow statements, not all queries.

Checkpoint, autovacuum, connection, disconnection, lock-wait, and temporary-file metrics also require the corresponding server logging settings. Message-based event parsing depends on the supported message language and format; SQLSTATE-based error classification does not depend on localized wording.

Give the service user read access to the selected logs and write access to its state directory. Keep log access restricted, because source files can contain SQL and client data.

## Alternatives and non-goals {#alternatives}

- Reading logs during `/metrics` adds parsing and persistence latency to database scrapes. A background worker keeps that work separate.
- File notifications can speed up discovery but cannot replace polling and reconciliation for correctness.
- Replaying all retained files on first start makes the initial counters depend on log retention. Starting at EOF gives an explicit baseline.
- Publishing before persistence can count records again after a crash. State is committed first.
- Dynamic labels and user patterns would make series counts and the saved schema depend on input. The metric catalog is fixed.
- A separate endpoint or executable would add a deployment unit for the same bounded data source. The existing process and endpoint are reused.

## Verification and remaining work {#acceptance}

The implementation is in `exporter/postgres_log*.go`. Tests use PostgreSQL 14, 16, and 18 fixtures. They cover quoted and multiline fields, partial records, rename, truncation, restart, locking, permissions, and crash points. They also cover event classification, series limits, conflicts, overlapping scrapes, and shutdown.

External CSV integration remains unverified. Set `PG_EXPORTER_TEST_PG_LOG_DIR` and validate real log rotation and restart recovery under the intended service user.

See [Composite Exporter](/design/composite-exporter/) for coordination. CSV definitions and logging settings are documented by [PostgreSQL 14](https://www.postgresql.org/docs/14/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) and [PostgreSQL 18](https://www.postgresql.org/docs/18/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG).
