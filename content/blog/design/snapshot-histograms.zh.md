---
title: "快照直方图是 Gauge，不是 Counter"
linkTitle: "快照直方图"
date: "2026-07-11T22:06:29+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
authors: [Vonng]
description: "为什么 PG Exporter 每次查询都重新构造 SQL 分布，并用 Gauge 序列暴露 bucket、count 与 sum"
summary: "已随 v1.4.0 发布。PG Exporter 在每次真实查询时重建 SQL 分布，并用 Gauge 暴露累计 bucket、count 与 sum，不把当前总体伪装成单调 Counter。"
categories: [design]
tags: [设计, Histogram, Prometheus, PostgreSQL]
---

> **决策状态：** 已随 [`v1.4.0`](https://github.com/pgsty/pg_exporter/releases/tag/v1.4.0) 发布。<br>
> **决策日期：** 2026-07-11；发布前于 2026-07-17 完成修订。<br>
> **适用范围：** PG Exporter v1.4.0 及后续版本中的 `HISTOGRAM` 列与内置 `pg_xact_age` 采集器。<br>
> **发布边界：** 本文描述已经发布的源码与指标契约；Dashboard 与 recording rule 仍由消费者负责。

PG Exporter 最初把每个 SQL 结果单元映射成标量 Gauge 或 Counter。它能回答“最老事务有多老”，却无法保留当前总体的分布形状。一个 30 分钟事务与一百个 18 秒事务可能具有相同最大值，但需要完全不同的处置方式。

第一版 Histogram 在不把 PG Exporter 变成有状态事件处理器的前提下补上了分布能力。它的核心决策只有一句话：

> PG Exporter Histogram 是一次真实 SQL 查询返回的全部行所重建的分布。它描述当前总体，而不是 exporter 进程启动以来累计看到的观测。

这句话决定了 exposition 类型、缓存、失败语义、PromQL 与 bucket 策略。

## 时间语义契约 {#temporal-contract}

参考总体是打开中的事务。事务开始时出现，随着时间经过移入更老的 bucket，在提交或回滚后消失。观测数和每个累计 bucket 都可能在两次抓取之间上升或下降。

普通 Prometheus Histogram 是累计 Counter：bucket、count，通常还有 sum，都会随时间增加。因此 Prometheus 的常规查询会先使用 `rate()`，再计算请求速率或时间窗口分布。这个假设不适用于每次重新生成的 SQL 快照。

所以 PG Exporter 把逻辑 Histogram 暴露成普通 Gauge 序列：

```text
pg_xact_age_seconds_bucket{datname="app",le="10"} 5
pg_xact_age_seconds_bucket{datname="app",le="30"} 9
pg_xact_age_seconds_bucket{datname="app",le="+Inf"} 11
pg_xact_age_seconds_count{datname="app"} 11
pg_xact_age_seconds_sum{datname="app"} 214
```

熟悉的命名和累计 `le` bucket 仍可供 `histogram_quantile()` 使用；Gauge 类型则如实表达所有值都可能下降。这是一项有意的语义折衷：输出具有经典 Histogram 的形状，但不是 Counter Histogram。

不要对这些序列应用 `rate()`、`irate()`、`increase()` 或 Counter reset 逻辑。应直接查询当前分布：

```promql
histogram_quantile(
  0.95,
  sum by (datname, le) (pg_xact_age_seconds_bucket)
)
```

当前平均值同样直接计算：

```promql
sum by (datname) (pg_xact_age_seconds_sum)
/
sum by (datname) (pg_xact_age_seconds_count)
```

## 配置与 SQL 契约 {#configuration-contract}

设计只增加一个用户可见的 usage：`HISTOGRAM`。

```yaml
- seconds:
    usage: HISTOGRAM
    bucket: [1, 3, 10, 30, 100, 300, 1000, 3000]
    description: Open transaction age snapshot in seconds
```

配置列中的每个非 NULL 值都是一次观测。具有相同完整标签元组的行属于同一个分布；同一查询中的多个 Histogram 列彼此独立聚合。

Bucket 是有限、包含上界的边界。配置加载阶段会拒绝空列表、重复值、非递增顺序、`NaN` 与无穷值。PG Exporter 自动追加 `+Inf`，用户不能自行配置。生成的 `le` 标签及 `_bucket`、`_count`、`_sum` 派生名称都是保留表面，冲突必须在抓取前失败。

`scale` 在 bucket 分配与求和之前生效；时间戳与布尔值沿用标量转换路径，不应用 scale。显式 `default` 会把 NULL 转成一次观测，否则忽略 NULL。

## 查询、缓存与原子性 {#atomicity}

每次真实 SQL 执行都从空 accumulator 开始。PG Exporter 对观测分组、分配有限 bucket、计算累计计数，并只在完整结果集验证成功后物化指标。

如果查询失败、缺少必需列，或任意观测无法转换成有限数值，本次执行中的标量与 Histogram family 都不会发布。失败在 collector query 边界上是原子的。

缓存命中只复用上一份不可变结果，不会再次累计同一批观测。下一次真实查询从零构造新快照，Histogram 状态不会跨执行保留。配置重载会丢弃旧 collector 与旧缓存，包括旧 bucket 布局。

这些规则让 Histogram 继续服从声明式 collector 模型：SQL 是权威数据源，TTL 决定查询是否执行，exporter 不发明第二个时间域。

## 为什么选择显式 Gauge 序列 {#alternatives}

几种看似更简单的方案被明确否决：

- `prometheus.NewConstHistogram` 会产生 Counter 风格的 Histogram 元数据；数值虽能编码，时间语义却是错误的。
- OpenMetrics GaugeHistogram 能更精确地表达语义，但 PG Exporter 使用经典 Prometheus 文本，没有理由为了一个采集类型引入 OpenMetrics 专用模式。
- Native Histogram 解决的是存储和分辨率问题，不会把不断变化的 SQL 总体变成累计事件流。
- 在 SQL 中预聚合 bucket 会让每个 collector 重复分组逻辑，并产生第二套配置契约。
- 跨抓取保留观测会把“当前数据库状态”改成“本 exporter 进程曾看到的事件”，随之引入重启、持久化和重复计数义务。

最终方案刻意保持狭窄：输入原始 SQL 观测，输出一份当前分布。

## 参考采集器与 bucket 演进 {#reference-collector}

第一版实现发布前围绕 `pg_xact_age` 完成修订：按数据库统计打开事务年龄与 idle-in-transaction 年龄，只保留 client backend，并采用适合即时运维问题的类对数 bucket 网格。目标查询是当前分位数、超过阈值的当前总体与当前均值。

以下 pgbench workload 用于制造多档 query time 与 hold time，验证实时分布。原设计目录不再承担文档权威，因此在这里保留可复现实例：

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

关键证据不是某个 benchmark 数字，而是：事务推进时 bucket 总体会移动和消失；缓存命中不会重复累计；重载新布局时不会保留旧样本。

## 结果与代价 {#consequences}

这个设计让用户无需有状态 exporter 就能得到可聚合的当前分布。代价是用户必须理解：这里的 `_bucket`、`_count`、`_sum` 后缀并不代表 Counter 时间语义。文档、Dashboard 与告警必须明确说明这一点。

完整语法由[采集器配置](/zh/config/#直方图列histogram)维护，已经交付的实现见 [v1.4.0 发布注记](/zh/release/v1.4.0/)。Prometheus 官方文档仍是普通 Counter Histogram 的权威，并解释了常规 `rate()` 查询为何依赖单调 count：[Histograms and summaries](https://prometheus.io/docs/practices/histograms/)。
