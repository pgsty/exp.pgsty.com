---
title: "Snapshot Histograms Are Gauges, Not Counters"
linkTitle: "Snapshot Histograms"
date: "2026-07-11T22:06:29+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "Why SQL snapshot distributions expose bucket, count, and sum as Gauge series"
summary: "Shipped in v1.4.0. Each SQL execution builds a fresh distribution. Buckets, count, and sum are Gauges and can decrease between scrapes."
categories: [design]
tags: [Design, Histogram, Prometheus, PostgreSQL]
---

A scalar metric cannot describe the distribution of a changing population. One 30-minute transaction and one hundred 18-second transactions have the same total age, but different counts, maxima, and operational effects.

> **Status:** Shipped in [v1.4.0](/release/v1.4.0/).<br>
> **Decision date:** 2026-07-11; revised on 2026-07-17.<br>
> **Last verified:** 2026-10-13.<br>
> **Scope:** `HISTOGRAM` columns and the `pg_xact_age` collector in stable `v1.4.1`, checked against development commit `c0ba58a`.<br>
> **Delivery:** Implementation, merge, release tag, and package publication completed. Focused local tests passed. Deployment and production operation remain unverified.

A PG Exporter snapshot Histogram groups the observations returned by one SQL execution. Each execution starts a new distribution. The exporter exposes its buckets, count, and sum as Gauge series because their values can decrease.

## Time semantics {#temporal-contract}

Open transactions appear when they start, move between age buckets, and disappear when they finish. This differs from a cumulative Histogram that counts events over time.

The output has the familiar bucket layout:

```text
pg_xact_age_seconds_bucket{datname="app",le="10"} 5
pg_xact_age_seconds_bucket{datname="app",le="30"} 9
pg_xact_age_seconds_bucket{datname="app",le="+Inf"} 11
pg_xact_age_seconds_count{datname="app"} 11
pg_xact_age_seconds_sum{datname="app"} 214
```

All three families are Gauges. Buckets are cumulative across their upper bounds within this snapshot, not across scrapes. Use `histogram_quantile()` directly:

```promql
histogram_quantile(
  0.95,
  sum by (datname, le) (pg_xact_age_seconds_bucket)
)
```

For the current mean age, divide sum by count:

```promql
sum by (datname) (pg_xact_age_seconds_sum)
/
sum by (datname) (pg_xact_age_seconds_count)
```

Do not use `rate()`, `irate()`, or `increase()` on these snapshot series. Those functions interpret decreases as counter resets.

## Configuration and SQL {#configuration-contract}

Declare an observation column with `usage: HISTOGRAM` and explicit bucket bounds:

```yaml
- seconds:
    usage: HISTOGRAM
    bucket: [1, 3, 10, 30, 100, 300, 1000, 3000]
    description: Open transaction age snapshot in seconds
```

Each non-NULL value is one observation. Rows with the same complete label tuple belong to one distribution. Multiple Histogram columns aggregate independently.

Bucket upper bounds are inclusive, finite, and strictly increasing. Configuration loading rejects empty lists, duplicates, `NaN`, and infinities. PG Exporter adds `+Inf` automatically. The `le` label and generated `_bucket`, `_count`, and `_sum` names are reserved; conflicting configuration is rejected.

`scale` applies before bucket assignment and summation. Timestamp and Boolean values use the scalar conversion rules and are not scaled. An explicit `default` turns NULL into an observation; otherwise NULL is ignored.

## Query, cache, and failure behavior {#atomicity}

Each SQL execution starts with empty accumulators. PG Exporter groups observations, calculates cumulative buckets, and publishes metrics after reading the complete result.

A query error, missing required column, or non-finite observation rejects the whole query result, including its scalar metrics. A failed refresh replaces the cached result with an empty result; it does not retain the previous distribution.

A cache hit returns the previous result without adding observations. The next SQL execution starts from zero. Reload discards the old collector and cache, including the old bucket layout.

## Alternatives and non-goals {#alternatives}

- `prometheus.NewConstHistogram` labels the data as a counter Histogram. Its time semantics do not match a changing SQL population.
- OpenMetrics GaugeHistogram describes the semantics directly, but would require a different exposition contract for this feature. Explicit Gauges work with the existing classic text endpoint.
- Native Histograms address storage and resolution. They do not change whether observations describe events or a current population.
- SQL could produce pre-aggregated buckets, but each collector would need to repeat the grouping logic.
- Retaining observations between scrapes would require event identity, restart handling, and duplicate prevention. Persistent event collection is outside this design; [log Histograms](/design/postgres-log-metrics/) have a separate contract.

## Reference collector and validation {#reference-collector}

`pg_xact_age` groups open transaction age and idle-in-transaction age by database. It selects client backends and uses a 10-second TTL. Its bucket grids support current quantiles, counts above a threshold, and mean age.

This pgbench workload creates several query and idle-in-transaction duration bands. Use it on a test database to observe transactions entering and leaving the buckets:

```sql
\set query_band random(1, 4)
\if :query_band = 1
  \set query_ms 300
\elif :query_band = 2
  \set query_ms 3000
\elif :query_band = 3
  \set query_ms 10000
\else
  \set query_ms 30000
\endif

\set hold_band random(1, 4)
\if :hold_band = 1
  \set hold_ms 300
\elif :hold_band = 2
  \set hold_ms 3000
\elif :hold_band = 3
  \set hold_ms 10000
\else
  \set hold_ms 30000
\endif

BEGIN;
SELECT pg_current_xact_id(), pg_sleep(:query_ms / 1000.0);
\sleep :hold_ms ms
COMMIT;
```

Tests cover independent Histogram columns, NULL handling, scaling, bucket boundaries, and query failures. They also cover cache reuse, deterministic output, concurrent collection, and reload.

## Consequences {#consequences}

The exporter provides aggregatable current distributions without keeping event history. Dashboard queries must use snapshot semantics even though the series use familiar Histogram suffixes.

See [Collector Configuration](/config/#histogram-columns-histogram) for syntax and [v1.4.0](/release/v1.4.0/) for the release. Prometheus explains ordinary cumulative Histogram queries in [Histograms and summaries](https://prometheus.io/docs/practices/histograms/).
