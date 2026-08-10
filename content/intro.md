---
title: "Introduction"
linkTitle: "Introduction"
description: "What pg_exporter does, how a scrape is planned, and where its operational boundaries lie"
weight: 10
icon: fa-solid fa-lightbulb
categories: [Concept]
---

`pg_exporter` turns PostgreSQL and PgBouncer runtime state into Prometheus metrics. Unlike an exporter with a fixed list of hard-coded queries, most of its metric surface is declared in YAML: a collector defines SQL, result columns, labels, metric types, eligibility rules, timeouts, and caching policy.

That design gives operators two useful properties at once:

- a release ships with a broad, tested default metric set;
- local teams can add, remove, or specialize metrics without rebuilding the binary.

## The Data Path

A normal scrape passes through six stages:

1. **Target selection** — the PostgreSQL URL comes from `--url`, environment, a secret file, or the local-first default.
2. **Fact discovery** — the exporter learns server version, recovery role, database inventory, extensions, schemas, and operator-supplied tags.
3. **Dynamic planning** — for each metric namespace, it selects the collector branch whose version range, role tags, custom tags, and predicates match the target.
4. **Query execution** — selected SQL runs with per-collector timeout and optional result caching.
5. **Metric conversion** — result columns become labels, gauges, counters, or snapshot histogram families.
6. **Exposition** — built-in and query-driven metrics are returned through the configurable Prometheus endpoint, normally `/metrics`.

Health and role-routing endpoints use a cached background-probe state rather than opening a new database query for every HTTP request. A health-check storm therefore does not become a database connection storm.

## Two Metric Layers

### Built-in exporter metrics

The Go binary always knows how to expose core availability and self-observation metrics such as:

- `pg_up`, `pg_version`, and `pg_in_recovery`;
- `pg_exporter_build_info` and exporter uptime;
- scrape counts, failures, durations, cache TTLs, and per-query statistics.

Use `--disable-intro` only when you intentionally want to hide exporter self-metrics. It does not remove YAML-defined business metrics.

### Declarative collector metrics

Everything else comes from [`pg_exporter.yml`](https://github.com/pgsty/pg_exporter/blob/main/pg_exporter.yml), which is generated from 58 ordered files under [`config/`](https://github.com/pgsty/pg_exporter/tree/main/config). The default bundle covers replication, WAL, checkpoints, activity, locks, transactions, database/object statistics, progress views, PgBouncer, and selected extensions.

See [Bundled Collectors](/collectors/) for the inventory and [Collector Configuration](/config/) for the schema.

## Failure Semantics

Failure is controlled at collector and process level:

- A collector with `fatal: true` can fail the scrape and reset the target's `*_up` metric.
- A non-fatal collector failure increments error statistics while other collectors continue.
- A query timeout defaults to 100 ms when omitted; a negative configured timeout disables the query deadline.
- Startup is non-blocking by default: HTTP starts even when the database is temporarily unavailable. `--fail-fast` changes this to an immediate startup failure.
- A valid hot reload replaces the active query set atomically; a rejected reload leaves the previous configuration running.

The `/explain` endpoint answers “why was this collector selected or skipped?”, while `/stat` answers “how did selected collectors perform?”. Together they are the first tools to use for missing, slow, or failing metrics.

## What pg_exporter Is Not

- It is not a PostgreSQL proxy and does not carry application traffic.
- It does not store time series; Prometheus, VictoriaMetrics, or another compatible system does that.
- It does not install extensions needed by optional collectors.
- It does not make an expensive SQL query safe merely because it is in YAML; operators still own query review, privileges, TTL, timeout, and cardinality.
- Its role endpoints report observed PostgreSQL state, not a distributed-consensus decision. They are useful inputs to routing, but HA policy remains with Patroni, the load balancer, and the operator.

## Project Status

The latest stable release is **v{{< param version >}}**. The default collector bundle covers PostgreSQL 10 through PostgreSQL 19 branches, while a separate legacy bundle covers PostgreSQL 9.1-9.6. PgBouncer collectors cover the `SHOW`-capable 1.8+ line through current 1.25+ schemas.

Continue with [Getting Started](/start/) for a minimal working deployment or [Production Deployment](/deploy/) for the full operational surface.
