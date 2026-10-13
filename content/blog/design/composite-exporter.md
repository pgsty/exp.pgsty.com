---
title: "One Endpoint, Several Sources: The Composite Exporter Contract"
linkTitle: "Composite Exporter"
date: "2026-08-11T23:50:55+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "Combine PostgreSQL and optional metric sources with fixed ownership and independent failure handling"
summary: "Implemented but unreleased. PostgreSQL remains authoritative. Live sources share a timeout; cached sources publish immutable snapshots."
categories: [design]
tags: [Design, Architecture, Prometheus, PgBouncer, Patroni]
---

Composite mode combines PostgreSQL, PgBouncer, Patroni, pgBackRest, and PostgreSQL log metrics in one `/metrics` endpoint. It reduces the number of processes and scrape targets for a database node. PostgreSQL remains the primary source; each optional source has its own failure and health state.

> **Status:** Implemented but unreleased.<br>
> **Decision date:** 2026-08-11; cached components added on 2026-08-23 and 2026-08-24.<br>
> **Last verified:** 2026-10-13.<br>
> **Scope:** Composite coordinator at source commit `c0ba58a`; absent from stable `v1.4.1`.<br>
> **Delivery:** Local tests passed. Not merged into `main` or tagged; packages, deployment, and production operation remain unverified.

## PostgreSQL remains authoritative {#primary-invariant}

Only a PostgreSQL gather error can make the Composite gather fail. A failure in an optional component affects that component's metrics and health. A valid PostgreSQL gather still produces an HTTP 200 response.

All optional components are disabled by default. With none enabled, startup creates no optional workers, clients, or file readers, and the scrape path uses no Composite coordination lock.

## Live collection and cached snapshots {#execution-models}

```text
Prometheus /metrics
        |
        v
Composite coordinator
  |-- PostgreSQL SQL       live, authoritative
  |-- PgBouncer SQL        live, optional
  |-- Patroni HTTP         live, optional
  |-- pgBackRest snapshot  cached, optional
  `-- PostgreSQL log       cached, optional
```

PostgreSQL and PgBouncer use the existing SQL collectors and their query caches. Patroni is fetched on each full scrape because role and leader state can change quickly.

pgBackRest and PostgreSQL logs use background workers. Each worker publishes an immutable snapshot. The HTTP request reads that snapshot, so command execution, log parsing, and state persistence do not delay database collection. See [cached pgBackRest metrics](/design/cached-pgbackrest-metrics/) and [durable PostgreSQL log metrics](/design/postgres-log-metrics/) for their refresh and recovery rules.

## Timeout and concurrent requests {#live-timeout}

PgBouncer and Patroni run concurrently under `--scrape-timeout`, which defaults to 10 seconds. PostgreSQL runs in parallel under its existing query timeouts. The optional deadline does not cancel PostgreSQL collection.

If a full Composite scrape is already running, an overlapping request collects PostgreSQL, process metrics, and cached snapshots. It omits live PgBouncer and Patroni collection and reports their component `up` values as zero for that response. It does not update their stored error counters or last-success timestamps. This prevents optional collection from building a request queue.

## Metric-family ownership {#family-ownership}

The ownership order for business metrics is:

```text
PostgreSQL > Patroni > PgBouncer > pgBackRest > PostgreSQL Log
```

Process and HTTP self-metrics are merged after PostgreSQL and before the optional sources. Component-health metrics are merged last.

The first source to own a metric-family name owns the whole family. A lower-priority source cannot append samples, even when the type, help text, and labels match. Histogram and Summary suffixes are also reserved: a higher-priority `foo` Histogram blocks a lower-priority `foo_count` family.

On a conflict, the conflicting family is omitted and the optional component reports a `gather` error. Its other valid families remain available.

## Patroni ingestion {#patroni-semantics}

PG Exporter fetches, parses, validates, and re-encodes Patroni's classic Prometheus text. It preserves family names, help text, types, labels, and sample values. It does not add a `component` label to business metrics.

The response limits are 1 MiB, 10,000 sample lines, and 256 metric families. HTTPS uses system trust roots and an optional `--http-ca-file`. Certificate errors mark Patroni down; there is no certificate-verification bypass flag.

## Component health {#health}

Composite mode exposes these self-metrics unless `--disable-intro` is set:

```text
pg_exporter_component_enabled{component="..."}
pg_exporter_component_up{component="..."}
pg_exporter_component_scrape_duration_seconds{component="..."}
pg_exporter_component_scrape_errors_total{component="...",reason="..."}
pg_exporter_component_last_success_timestamp_seconds{component="..."}
```

`enabled` identifies configured components, including zero for disabled ones. `up` reports the collection outcome. The duration and last-success time describe a scrape for live sources and a background cycle for cached sources. Error reasons come from a fixed list, such as `connect`, `timeout`, `tls`, `parse`, and `gather`.

The existing `/up`, `/health`, `/primary`, and `/replica` routes continue to describe PostgreSQL. They are used for database health checks and routing, so optional components do not change their meaning. `--disable-intro` removes self-metrics and retains business metrics.

## Alternatives and non-goals {#alternatives}

- Separate exporters offer process isolation but require separate targets, packages, and service configuration. Composite mode is an optional deployment choice.
- Sequential collection makes the total latency depend on the order of sources. Concurrent live collection shares one optional timeout.
- Raw Patroni passthrough cannot enforce metric ownership or response limits. Parsing provides both checks.
- A generic plugin registry would expose lifecycle and precedence rules before the integrations were stable. This design uses named components and fixed precedence.
- An “all sources must succeed” policy would make database monitoring depend on optional services. The coordinator keeps failures local.

The design does not change metric namespaces or migrate Pigsty targets, dashboards, alerts, or existing standalone exporters.

## Verification and consequences {#consequences}

The contract is implemented in `exporter/composite.go`, `exporter/patroni.go`, and the startup and reload paths. Tests cover disabled behavior, timeouts, TLS and format errors, family conflicts, concurrent requests, reload, and shutdown.

One process now needs the permissions for every enabled source. Grant only those permissions. Before replacing a standalone exporter, validate the released package, target labels, dashboards, and alerts in the destination environment.
