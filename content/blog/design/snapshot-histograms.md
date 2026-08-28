---
title: "Snapshot Histograms Are Gauges, Not Counters"
linkTitle: "Snapshot Histograms"
date: "2026-07-11T22:06:29+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
authors: [Vonng]
description: "Why PG Exporter rebuilds SQL distributions on every query and exposes their buckets, count, and sum as gauge series"
summary: "Shipped in v1.4.0. PG Exporter rebuilds SQL distributions on every real query and exposes their cumulative buckets, count, and sum as Gauge series rather than pretending they are monotonic counters."
categories: [design]
tags: [Design, Histogram, Prometheus, PostgreSQL]
---

> **Decision status:** Shipped in [`v1.4.0`](https://github.com/pgsty/pg_exporter/releases/tag/v1.4.0).<br>
> **Decision date:** 2026-07-11; amended on 2026-07-17 before release.<br>
> **Applies to:** `HISTOGRAM` columns and the bundled `pg_xact_age` collector in PG Exporter v1.4.0 and later.<br>
> **Release boundary:** this article describes a released source and metric contract; dashboards and recording rules remain consumer responsibilities.

PG Exporter originally mapped each SQL result cell to a scalar Gauge or Counter. That model could answer questions such as “how old is the oldest transaction?”, but it could not preserve the shape of the current population. A database with one 30-minute transaction and a database with one hundred 18-second transactions could produce the same maximum while requiring very different action.

The first Histogram design added a distribution without turning PG Exporter into a stateful event processor. Its defining decision is simple:

> A PG Exporter Histogram is a distribution rebuilt from the rows returned by one real SQL query execution. It describes the current population, not observations accumulated since process start.

That sentence determines the exposition type, cache behavior, failure semantics, PromQL, and bucket policy.

## The temporal contract {#temporal-contract}

The reference population is open transactions. A transaction appears when it starts, moves to older buckets as time passes, and disappears when it commits or rolls back. The number of observations and every cumulative bucket may rise or fall between scrapes.

Ordinary instrumented Prometheus histograms are cumulative counters: their bucket, count, and normally their sum series increase over time. Prometheus therefore teaches users to apply `rate()` before computing request rates or time-window distributions. That assumption is wrong for a fresh SQL snapshot.

PG Exporter consequently emits the logical Histogram as ordinary Gauge series:

```text
pg_xact_age_seconds_bucket{datname="app",le="10"} 5
pg_xact_age_seconds_bucket{datname="app",le="30"} 9
pg_xact_age_seconds_bucket{datname="app",le="+Inf"} 11
pg_xact_age_seconds_count{datname="app"} 11
pg_xact_age_seconds_sum{datname="app"} 214
```

The familiar names and cumulative `le` buckets preserve compatibility with `histogram_quantile()`. The Gauge type preserves the truth that all values may decrease. This is a deliberate semantic compromise: the output looks like a classic histogram family but is not a counter histogram.

Never apply `rate()`, `irate()`, `increase()`, or counter-reset logic to these series. Query the current distribution directly:

```promql
histogram_quantile(
  0.95,
  sum by (datname, le) (pg_xact_age_seconds_bucket)
)
```

The current mean is equally direct:

```promql
sum by (datname) (pg_xact_age_seconds_sum)
/
sum by (datname) (pg_xact_age_seconds_count)
```

## Configuration and SQL contract {#configuration-contract}

The design adds one user-facing usage, `HISTOGRAM`:

```yaml
- seconds:
    usage: HISTOGRAM
    bucket: [1, 3, 10, 30, 100, 300, 1000, 3000]
    description: Open transaction age snapshot in seconds
```

Each non-NULL value in the configured column is one observation. Rows with the same complete label tuple belong to the same distribution. Multiple Histogram columns in one query aggregate independently.

Buckets are inclusive finite upper bounds. Configuration loading rejects an empty list, duplicates, non-increasing order, `NaN`, and infinities. PG Exporter appends `+Inf`; users must not configure it. The generated `le` label and the derived `_bucket`, `_count`, and `_sum` names are reserved, so collisions fail before scraping.

`scale` is applied before bucket assignment and summation. Timestamp and Boolean values follow the existing scalar conversion path and are exempt from scaling. An explicit `default` converts NULL into an observation; otherwise NULL is ignored.

## Query, cache, and atomicity {#atomicity}

A real SQL execution starts with empty accumulators. PG Exporter groups observations, assigns finite buckets, produces cumulative counts, and materializes the result only after the complete result set is valid.

If the query fails, a required column is missing, or any observation cannot be converted to a finite number, no scalar or Histogram family from that execution is published. The failure is atomic at the collector-query boundary.

A cache hit reuses the previous immutable result. It does not add the same observations again. A subsequent real query creates a new snapshot from zero; no Histogram state survives between executions. Reloading configuration discards the old collector and its cached snapshot, including an old bucket layout.

These rules keep Histogram semantics aligned with the declarative collector model: SQL remains the source of truth, TTL controls query execution, and the exporter does not invent a second time domain.

## Why explicit Gauge series won {#alternatives}

Several apparently simpler alternatives were rejected:

- `prometheus.NewConstHistogram` creates counter-like Histogram metadata. It can encode the numbers but misstates their temporal behavior.
- A formal OpenMetrics GaugeHistogram would express the semantics more precisely, but PG Exporter served the classic Prometheus text format and did not require an OpenMetrics-only mode for one collector type.
- Native Histograms solve different storage and resolution problems. They do not turn a changing SQL population into a cumulative event stream.
- Pre-aggregating buckets in SQL would duplicate grouping logic in every collector and create two configuration contracts.
- Retaining observations across scrapes would change “current database state” into “events seen by this exporter process”, with restart, persistence, and double-counting obligations.

The selected design is narrower: raw SQL observations in, one current distribution out.

## Reference collector and bucket evolution {#reference-collector}

The first implementation was refined before release around `pg_xact_age`, a per-database distribution of open transaction age and idle-in-transaction age. The final collector filters to client backends and uses logarithmic-style bucket grids suitable for instant operational questions: current quantiles, population above a threshold, and current mean.

The following pgbench workload was used to create several query and hold-time bands for live acceptance. It is reproduced here because the original design directory is no longer the documentation authority:

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

The important evidence was not a particular benchmark number. It was that bucket populations moved and disappeared as transactions advanced, cache hits did not accumulate them, and reload installed a new layout without retaining old samples.

## Consequences {#consequences}

The design gives users aggregatable current distributions without a stateful exporter. In return, users must understand that the `_bucket`, `_count`, and `_sum` suffixes do not imply counter temporality here. Documentation, dashboards, and alerts must state that distinction explicitly.

The complete collector syntax is maintained in [Collector Configuration](/config/#histogram-columns-histogram), and the shipped implementation is summarized in the [v1.4.0 release note](/release/v1.4.0/). Prometheus' documentation remains the authority for ordinary counter histograms and explains why their usual `rate()`-based queries depend on monotonic counts: [Histograms and summaries](https://prometheus.io/docs/practices/histograms/).
