---
title: "Caching pgBackRest Metrics Outside the Scrape Path"
linkTitle: "Cached pgBackRest Metrics"
date: "2026-08-23T19:34:09+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "Run pgBackRest in a bounded background worker and serve the latest valid metrics snapshot"
summary: "Implemented but unreleased. Background collection keeps command and repository latency out of Prometheus requests. Failed refreshes retain the last valid backup state."
categories: [design]
tags: [Design, pgBackRest, Prometheus, Reliability]
---

`pgbackrest info --output=json` reports backup state. The command can contact remote repositories and wait for storage. Running it during a Prometheus request would add that delay to database monitoring.

> **Status:** Implemented but unreleased.<br>
> **Decision date:** 2026-08-23.<br>
> **Last verified:** 2026-10-13.<br>
> **Scope:** Optional `--pgbackrest` component at source commit `c0ba58a`; absent from stable `v1.4.1`.<br>
> **Delivery:** Local tests passed. Not merged into `main` or tagged; packages, deployment, and production operation remain unverified.

PG Exporter therefore runs pgBackRest in a background worker. The worker validates the result and publishes an immutable snapshot. `/metrics` reads the latest snapshot without waiting for a command.

```text
background worker
    -> detect pgBackRest version
    -> run info --output=json
    -> validate and build metrics
    -> publish snapshot

/metrics request
    -> read snapshot
    -> merge with other sources
```

## Execution limits {#bounded-execution}

The worker executes the configured program directly, without a shell.

| Control | Default | Rule |
| --- | ---: | --- |
| Command | `pgbackrest` | Fixed version and info arguments |
| Refresh interval | 2 minutes | Minimum 10 seconds |
| Refresh timeout | 30 seconds | One deadline for version detection and info |
| Standard output | 16 MiB | Overflow cancels the command |
| Standard error | 64 KiB | Overflow cancels the command |

The worker first runs `version --output=num`. For older versions, it falls back to `version`. It then runs `info --output=json`. Cancellation stops the direct child process; a one-second wait delay bounds cleanup of output pipes.

## Validate before publication {#validation}

A zero command exit status is not sufficient. The output must have the expected JSON structure, valid numeric fields, and consistent stanza and repository references. Validation also limits the input to 256 stanzas and 4,096 backups, and the output to 20,000 samples and 4 MiB of Prometheus text.

Only a complete valid result replaces the snapshot. Metric families are validated before publication, so the scrape path only needs to check their headers and ownership.

pgBackRest follows PostgreSQL, process self-metrics, Patroni, and PgBouncer in the [Composite ownership order](/design/composite-exporter/#family-ownership). A conflicting family is omitted and marks the component down. Other valid families remain available.

## Retain the last successful result {#last-good}

After the first successful refresh, a command, timeout, parse, or limit error preserves the previous business metrics. The component reports `up=0`, increments its error counter, and keeps the previous last-success timestamp.

Backup-age gauges are recalculated from the retained JSON during failed background refreshes. They continue to reflect elapsed time at the refresh interval. `/metrics` does not parse JSON or execute pgBackRest.

Before the first success, no backup business metrics are available. PostgreSQL and the other valid sources continue to work.

## Health and concurrent requests {#health}

Component health uses `component="pgbackrest"`. `up` describes the latest collection result; the last-success timestamp shows how old the backup data is. Command failures use `exec`, output limits use `limit` for standard output, and parse or merge errors use their corresponding reasons. Standard-error overflow is classified as an execution error.

Overlapping scrapes can read the same snapshot. They do not start another command or update the stored component-health history. Metric conflicts still follow the Composite ownership rule.

## Alternatives and non-goals {#alternatives}

Running the command on every scrape would couple Prometheus timeouts and concurrent requests to repository work. A background worker gives command execution a separate timeout and refresh interval.

A separate exporter offers process isolation but adds a service, port, package, and target. The integrated component offers another deployment option. It does not migrate existing deployments automatically.

A generic shell-command plugin was rejected because pgBackRest requires specific JSON validation, version handling, metric definitions, and recovery rules. This component accepts a pgBackRest executable, not arbitrary command templates.

## Verification and operation {#consequences}

`exporter/pgbackrest.go` owns command execution and snapshot publication; `exporter/pgbackrest_metrics.go` owns JSON validation and metrics. Tests cover version fallback, malformed and oversized output, timeout, last-success retention, family conflicts, and shutdown.

The service user needs permission to run pgBackRest and read its configuration and repository credentials. The PG Exporter package does not bundle pgBackRest. Use the host's backup installation.

Alert on component health and last-success age. Existing backup metrics can remain visible after collection fails. Before replacing a standalone exporter, compare both outputs against the same repository under the intended service user.
