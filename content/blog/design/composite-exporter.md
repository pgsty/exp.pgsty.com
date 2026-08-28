---
title: "One Endpoint, Several Sources: The Composite Exporter Contract"
linkTitle: "Composite Exporter"
date: "2026-08-11T23:50:55+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
authors: [Vonng]
description: "How PG Exporter combines PostgreSQL, PgBouncer, Patroni, and cached components without weakening the primary PostgreSQL scrape"
summary: "Implemented but unreleased. PostgreSQL remains authoritative while live and cached optional components share one endpoint through bounded timeouts, deterministic family ownership, and local failure isolation."
categories: [design]
tags: [Design, Architecture, Prometheus, PgBouncer, Patroni]
---

> **Decision status:** Implemented in a development line; not present in `main`, a tag, or a published package as of 2026-08-28.<br>
> **Decision date:** 2026-08-11; extended by cached components on 2026-08-23 and 2026-08-24.<br>
> **Applies to:** the optional Composite coordinator for PostgreSQL, PgBouncer, Patroni, pgBackRest, and PostgreSQL CSV log metrics.<br>
> **Release boundary:** design and implementation evidence exist; merge, tag, package, deployment, and production replacement remain separate gates.

PG Exporter began as a declarative SQL exporter for one PostgreSQL-compatible target. A Pigsty node, however, also exposes useful state through PgBouncer's admin database, Patroni's Prometheus endpoint, pgBackRest's local command, and PostgreSQL's structured logs. Running one exporter per source is operationally simple at first, but it creates several targets, ports, labels, health conventions, and lifecycle owners for what operators understand as one database instance.

The Composite design allows one PG Exporter process to expose those sources on the existing `/metrics` endpoint. Its purpose is not merely to concatenate metrics. Its purpose is to make the failure and ownership rules explicit enough that adding optional components can never weaken the original PostgreSQL contract.

## The non-negotiable invariant {#primary-invariant}

PostgreSQL remains mandatory and authoritative. Only the PostgreSQL collector's gather error may become the fatal error returned by the composite gatherer. PgBouncer, Patroni, pgBackRest, or log-metric failures may remove their own data and set their own health, but they must not turn an otherwise valid PostgreSQL response into HTTP 500.

This rule addresses the most dangerous failure mode of a combined endpoint: a TLS error in an optional Patroni request, a slow backup repository, or a malformed log record must not hide the database metrics that operators need to diagnose the incident.

All optional components are disabled by default. When their flags and URLs are empty, PG Exporter does not create their collectors, issue requests, execute commands, scan files, register component health, or add a coordination lock to the old scrape path.

## One coordinator, three execution models {#execution-models}

The sources do not have the same latency or freshness contract, so they should not share one generic adapter:

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

PostgreSQL keeps the established real-time SQL path. PgBouncer also runs SQL on each scrape because its queries are cheap and the existing exporter semantics are already useful. Patroni is fetched live because role, leader, DCS, and timeline state can change immediately.

pgBackRest and PostgreSQL logs use background workers and immutable snapshots. Executing a backup command or scanning log files inside a Prometheus request would make database metric availability depend on disk, repository, parser, and persistence latency. Their detailed contracts are recorded in [Caching pgBackRest Metrics Outside the Scrape Path](/design/cached-pgbackrest-metrics/) and [Turning PostgreSQL CSV Logs into Durable Metrics](/design/postgres-log-metrics/).

## Live work is bounded and concurrent {#live-timeout}

PgBouncer and Patroni run concurrently under one sidecar timeout, which defaults to 10 seconds. PostgreSQL runs in parallel but is not canceled by that optional deadline. This prevents a sidecar budget from becoming a new timeout for the authoritative query path.

The coordinator also refuses to queue overlapping Prometheus requests behind optional live work. If another full Composite scrape is already running, the overlapping request gathers PostgreSQL, process metrics, and the lock-free cached snapshots. It marks or omits live optional work instead of waiting for the earlier request.

This is a degradation policy, not an optimization detail. A scrape storm should reduce optional completeness before it increases latency or goroutine queues on the primary path.

## Metric-family ownership {#family-ownership}

Combining registries requires a deterministic rule for identical family names. The selected order is:

```text
PostgreSQL > Patroni > PgBouncer > pgBackRest > PostgreSQL Log
```

Process and HTTP self-metrics are merged behind PostgreSQL as well. A lower-priority source may add a family only when no higher-priority source owns that name or any reserved Histogram/Summary derivative. It may not append samples to an existing family merely because Help, type, and labels happen to match.

This whole-family rule avoids a subtle invalid state in which two components partially co-own one metric. It also blocks collisions such as a literal `foo_count` beside a higher-priority `foo` Histogram. Non-conflicting families from a partially rejected optional component remain useful; the conflict marks that component down with reason `gather` but does not alter the PostgreSQL result.

## Patroni is parsed, not blindly proxied {#patroni-semantics}

Patroni already exposes Prometheus metrics, but byte concatenation would bypass validation and create an invalid response if it emitted conflicting metadata, OpenMetrics-only syntax, excessive data, or a duplicate family. The Composite collector therefore fetches, parses, validates, and re-encodes supported classic Prometheus semantics.

The design preserves Patroni family names, Help, types, labels, and sample values. It deliberately does not rename every metric or add a `component` label. Source identity belongs in the target labels and component-health surface, not in every business series.

Outbound HTTPS uses system roots plus an optional CA file. The design does not add `insecure_skip_verify`; a certificate failure is visible as a Patroni component failure instead of silently weakening transport verification.

## Health is not one Boolean {#health}

Each enabled component has a bounded health surface:

```text
pg_exporter_component_enabled{component="..."}
pg_exporter_component_up{component="..."}
pg_exporter_component_scrape_duration_seconds{component="..."}
pg_exporter_component_scrape_errors_total{component="...",reason="..."}
pg_exporter_component_last_success_timestamp_seconds{component="..."}
```

These signals answer different questions. `enabled` is configuration state. `up` is the latest component outcome. `last_success` shows staleness. Error counters preserve bounded reasons such as connect, timeout, TLS, parse, gather, command execution, state, or source failure.

They do not replace PostgreSQL's existing `/up`, `/health`, `/primary`, or `/replica` semantics. Those routes continue to describe the PostgreSQL target. Turning them into “all components healthy” would break routing and failover users that never opted into a composite availability definition.

`--disable-intro` suppresses exporter and component self-metrics, not business metrics. This preserves the existing meaning of that flag.

## Alternatives rejected {#alternatives}

The design intentionally refused several broader abstractions:

- A generic plugin registry would make the first integration harder to audit and would expose lifecycle and precedence as public extension APIs before real components stabilized them.
- Sequential collection would let one optional source consume the full request budget before the next source ran.
- Byte-level Patroni passthrough would avoid a parse step but give up conflict, protocol, and resource validation.
- A `component` label on every family would change established metric contracts and multiply series without resolving name ownership.
- A global “all sources must succeed” policy would make optional integrations reduce availability.
- Replacing every standalone exporter and Pigsty target in the same change would mix source correctness with deployment migration and remove rollback options.

The selected design is explicit rather than universal: named components, a fixed ownership order, separate live and cached paths, and PostgreSQL-first failure semantics.

## Consequences and release gates {#consequences}

Composite mode can reduce target and process count while preserving existing namespaces. In return, one process now owns more credentials, network clients, parsers, background workers, and health states. Operators must grant only the permissions needed by enabled components and must treat family conflicts as configuration or compatibility defects.

The implementation existing in a development tree is not evidence that a stable release, Pigsty target migration, dashboard update, recording rule, alert, or old-process retirement has happened. Those gates must be verified independently when the feature reaches a public branch and release.
