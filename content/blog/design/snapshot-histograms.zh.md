---
title: "快照直方图是 Gauge，不是 Counter"
linkTitle: "快照直方图"
date: "2026-07-11T22:06:29+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "为什么 SQL 快照分布将桶、计数与总和输出为 Gauge 序列"
summary: "已随 v1.4.0 发布。每次 SQL 执行重建分布；桶、计数和总和均为 Gauge，可在抓取之间下降。"
categories: [design]
tags: [设计, Histogram, Prometheus, PostgreSQL]
---

一个标量指标无法描述变化中的总体分布。一个 30 分钟事务与一百个 18 秒事务的总年龄相同，但数量、最大年龄和运维影响不同。

> **状态：** 已随 [v1.4.0](/zh/release/v1.4.0/) 发布。<br>
> **决策日期：** 2026-07-11；2026-07-17 修订。<br>
> **最后核验：** 2026-11-09。<br>
> **范围：** 稳定版 `v1.6.0` 的 `HISTOGRAM` 列与 `pg_xact_age` 采集器，并对照 `6bee809` 与开发提交 `c0ba58a` 核验。<br>
> **交付进度：** 已实现、合并、打标签并发布软件包。针对性本地测试已通过；部署与生产运行未核验。

PG Exporter 快照直方图对一次 SQL 执行返回的观测值分组。每次执行都重建分布。由于值可能下降，桶、计数和总和都以 Gauge 序列输出。

## 时间语义 {#temporal-contract}

事务开始时进入总体，随时间增长移入更大的年龄桶，结束时离开总体。这与持续累计事件的 Histogram 不同。

输出沿用常见的桶结构：

```text
pg_xact_age_seconds_bucket{datname="app",le="10"} 5
pg_xact_age_seconds_bucket{datname="app",le="30"} 9
pg_xact_age_seconds_bucket{datname="app",le="+Inf"} 11
pg_xact_age_seconds_count{datname="app"} 11
pg_xact_age_seconds_sum{datname="app"} 214
```

这三个指标族都是 Gauge。桶内计数按当前快照的上界累计，不跨抓取累计。直接使用 `histogram_quantile()`：

```promql
histogram_quantile(
  0.95,
  sum by (datname, le) (pg_xact_age_seconds_bucket)
)
```

当前平均年龄由总和除以计数得到：

```promql
sum by (datname) (pg_xact_age_seconds_sum)
/
sum by (datname) (pg_xact_age_seconds_count)
```

不要对这些快照序列使用 `rate()`、`irate()` 或 `increase()`。这些函数会把数值下降解释为计数器重置。

## 配置与 SQL {#configuration-contract}

用 `usage: HISTOGRAM` 声明观测列，并指定桶上界：

```yaml
- seconds:
    usage: HISTOGRAM
    bucket: [1, 3, 10, 30, 100, 300, 1000, 3000]
    description: Open transaction age snapshot in seconds
```

每个非 NULL 值是一次观测。完整标签元组相同的行归入同一分布；多个 Histogram 列独立聚合。

桶包含上界，边界必须有限且严格递增。配置加载时拒绝空列表、重复值、`NaN` 和无穷值。PG Exporter 自动追加 `+Inf`。`le` 标签及生成的 `_bucket`、`_count`、`_sum` 名称为保留名称，冲突配置会被拒绝。

`scale` 在分桶和求和前生效。时间戳与布尔值沿用标量转换规则，不进行缩放。显式 `default` 将 NULL 转为观测值；未指定时忽略 NULL。

## 查询、缓存与失败行为 {#atomicity}

每次 SQL 执行都从空累加器开始。PG Exporter 对观测分组、计算累计桶，并在读完全部结果后发布指标。

查询出错、缺少必需列或出现非有限观测值时，整份查询结果都被拒绝，包括同一查询的标量指标。刷新失败会将缓存替换为空结果，不保留上一份分布。

缓存命中直接返回上一份结果，不追加观测。下一次 SQL 执行从零开始。重载丢弃旧采集器和缓存，包括旧桶布局。

## 备选方案与非目标 {#alternatives}

- `prometheus.NewConstHistogram` 将数据标为 Counter Histogram，其时间语义不适合变化中的 SQL 总体。
- OpenMetrics GaugeHistogram 能直接表达该语义，但需要为此功能改变输出协议。显式 Gauge 可沿用经典文本端点。
- Native Histogram 解决存储和分辨率问题，不改变观测是事件还是当前总体这一事实。
- 在 SQL 中预聚合桶，会让每个采集器重复分组逻辑。
- 跨抓取保留观测需要事件身份、重启处理和去重。持久事件采集不在本设计范围内；[日志 Histogram](/zh/design/postgres-log-metrics/) 使用独立契约。

## 参考采集器与验证 {#reference-collector}

`pg_xact_age` 按数据库统计未结束事务的年龄和事务内空闲时长，只选择客户端后端，TTL 为 10 秒。其桶边界支持计算当前分位数、超过阈值的数量和平均年龄。

以下 pgbench 脚本产生多档查询时长和事务内空闲时长。可在测试数据库中运行，观察事务进入和离开各桶：

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

实现与测试覆盖多个 Histogram 列独立聚合、NULL、缩放、桶边界、查询失败、缓存复用、确定性输出、并发采集与重载。

## 运维影响 {#consequences}

Exporter 无需保存事件历史，就能提供可聚合的当前分布。虽然序列使用常见 Histogram 后缀，仪表盘查询仍须遵循快照语义。

完整语法见[采集器配置](/zh/config/#histogram-columns-histogram)，发布内容见 [v1.4.0](/zh/release/v1.4.0/)。普通累计 Histogram 的查询方法见 Prometheus [Histograms and summaries](https://prometheus.io/docs/practices/histograms/)。
