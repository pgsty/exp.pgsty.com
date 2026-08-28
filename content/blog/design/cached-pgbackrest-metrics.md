---
title: "Caching pgBackRest Metrics Outside the Scrape Path"
linkTitle: "Cached pgBackRest Metrics"
date: "2026-08-23T19:34:09+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
authors: [Vonng]
description: "Why PG Exporter executes pgBackRest in a bounded background worker and serves an immutable last-good snapshot"
summary: "Implemented but unreleased. A bounded background worker validates pgBackRest output and atomically publishes a last-good snapshot, keeping command and repository latency outside Prometheus requests."
categories: [design]
tags: [Design, pgBackRest, Prometheus, Reliability]
---

> **Decision status:** Implemented in a development line; not present in `main`, a tag, or a published package as of 2026-08-28.<br>
> **Decision date:** 2026-08-23.<br>
> **Applies to:** the optional `--pgbackrest` cached component inside the Composite exporter.<br>
> **Release boundary:** source-level behavior has been implemented and tested; public release, packaging, deployment, and retirement of a standalone exporter remain unverified.

pgBackRest exposes rich backup state through `pgbackrest info --output=json`, but it exposes that state through a command, not a low-latency metrics endpoint. The command may inspect local configuration, contact remote repositories, wait on storage, emit large JSON, or fail for reasons unrelated to PostgreSQL SQL metrics.

Executing it during every Prometheus request would couple the availability and latency of the primary database scrape to backup infrastructure. The selected design therefore treats pgBackRest as a cached component:

```text
background worker
    -> pgbackrest version
    -> pgbackrest info --output=json
    -> strict validation and metric construction
    -> atomic immutable snapshot

/metrics request
    -> load current snapshot
    -> merge below PostgreSQL, Patroni, and PgBouncer
```

The command path and scrape path never wait for one another.

## Bounded command execution {#bounded-execution}

The collector executes the configured binary directly, without a shell. The production defaults are:

| Control | Default | Contract |
| --- | ---: | --- |
| Command | `pgbackrest` | Executed directly with fixed arguments |
| Refresh interval | 2 minutes | Must be at least 10 seconds |
| Refresh timeout | 30 seconds | Covers one background refresh |
| Standard output | 16 MiB | Hard limit; overflow cancels the command |
| Standard error | 64 KiB | Hard diagnostic limit |

The worker first detects the pgBackRest version, preferring numeric output and falling back to the older text form when necessary. It then runs `info --output=json`. Version and JSON shape are validated together because supported fields and known compatibility cases vary across pgBackRest releases.

Limits are part of the security and reliability contract. A corrupt repository, unexpected command, or hostile wrapper must not allocate unbounded memory or leave a child process running after overflow. The runner also uses a short wait delay after cancellation so process cleanup cannot stall indefinitely.

## Validate before publication {#validation}

A successful command is not yet a successful refresh. The JSON must satisfy the expected document shape, bounded object counts, numeric constraints, stanza and repository relationships, and metric-name and label rules. The resulting Prometheus families are normalized before publication.

Only a complete valid candidate replaces the current snapshot. Prometheus requests can then use a cheaper merge path: the cached families have already passed full client-library validation, so each database scrape checks ownership and headers without revalidating the entire backup payload.

The Composite ownership order remains:

```text
PostgreSQL > Patroni > PgBouncer > pgBackRest > PostgreSQL Log
```

A pgBackRest family that conflicts with a higher-priority owner is omitted and marks the component down. It cannot append samples to the existing family and cannot make the PostgreSQL gather fatal.

## Last-good semantics {#last-good}

After one successful refresh, a later command, timeout, parse, or limit failure keeps the previous business families. The component reports `up=0`, increments a bounded error reason, and preserves the timestamp of the last success.

This is not “pretend the backup source is healthy”. It is a deliberate split between two facts:

- the newest refresh failed;
- the last valid backup state is still useful if its age is visible.

Relative backup-age gauges continue to advance during a failure. The worker retains the last valid JSON and version and may rebuild only those time-relative values in the background. `/metrics` itself never reparses JSON or executes pgBackRest.

Before the first successful refresh there is no last-good business snapshot to serve. Health stays down and the endpoint still returns PostgreSQL plus any other valid components.

## Health and overlapping scrapes {#health}

The cached component participates in the common health surface with `component="pgbackrest"`. Its failure reasons include command execution and resource limit in addition to connection-independent parse and gather failures.

An overlapping Prometheus request does not queue behind a full Composite scrape. It reads the same atomic pgBackRest snapshot and includes it when its families do not conflict. Cached data therefore remains available during overlap without starting a second command or mutating component health from the request path.

## Why not run on every scrape {#alternatives}

Running the command on demand would provide superficially fresher data, but would produce several undesirable contracts:

- Prometheus timeout would become a backup-command timeout.
- Concurrent scrapes could execute concurrent repository inspections.
- Repository latency could hide PostgreSQL metrics.
- A scrape storm could amplify load on local and remote storage.
- Command output size and process cleanup would become HTTP-handler concerns.

A separate exporter process provides stronger process isolation, but retains another port, target, package, and health model. Composite mode offers a migration option without claiming that every environment must retire the standalone process immediately.

A universal command-plugin framework was also rejected. pgBackRest's JSON, version compatibility, security, metrics, and last-good semantics are domain-specific. Treating it as arbitrary shell output would weaken validation while making an unstable plugin API part of the product.

## Operational consequences {#consequences}

Enabling the component grants the PG Exporter service permission to execute pgBackRest and read its configuration. The official PG Exporter package does not need to bundle the pgBackRest binary; the executable and repository credentials remain owned by the host's backup installation.

Operators must alert on component health and last-success age, not merely the continued presence of backup metrics. They must also validate the final package and service user against real repositories before replacing a standalone exporter. Source tests, a tagged release, a packaged binary, a Pigsty target change, and production parity are separate acceptance gates.

The surrounding coordinator and failure rules are documented in [One Endpoint, Several Sources](/design/composite-exporter/).
