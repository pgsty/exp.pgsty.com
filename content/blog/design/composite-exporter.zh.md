---
title: "一个端点，多种来源：Composite Exporter 契约"
linkTitle: "Composite Exporter"
date: "2026-08-11T23:50:55+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
authors: [Vonng]
description: "PG Exporter 如何组合 PostgreSQL、PgBouncer、Patroni 与缓存组件，同时不削弱 PostgreSQL 主抓取"
summary: "已实现但未发布。PostgreSQL 始终权威；实时与缓存可选组件通过有界超时、确定性 family 所有权和局部失败隔离共享同一个端点。"
categories: [design]
tags: [设计, 架构, Prometheus, PgBouncer, Patroni]
---

> **决策状态：** 已在开发线实现；截至 2026-08-28，尚未进入 `main`、tag 或公开软件包。<br>
> **决策日期：** 2026-08-11；2026-08-23 与 2026-08-24 又增加了缓存组件。<br>
> **适用范围：** PostgreSQL、PgBouncer、Patroni、pgBackRest 与 PostgreSQL CSV 日志指标的可选 Composite 协调层。<br>
> **发布边界：** 已有设计与实现证据；合并、tag、软件包、部署和生产替换仍是独立门槛。

PG Exporter 最初是针对一个 PostgreSQL 兼容目标的声明式 SQL Exporter。但在一台 Pigsty 节点上，PgBouncer 管理库、Patroni Prometheus 端点、pgBackRest 本地命令和 PostgreSQL 结构化日志同样包含重要状态。为每种来源各运行一个 exporter 初看简单，却会为同一个数据库实例产生多个 target、端口、标签、健康语义和生命周期责任人。

Composite 设计允许一个 PG Exporter 进程在现有 `/metrics` 上暴露这些来源。它的目标不是简单拼接指标，而是把失败和所有权规则定义到足够精确，使新增可选组件永远不会削弱原有 PostgreSQL 契约。

## 不可协商的主线不变量 {#primary-invariant}

PostgreSQL 始终必选并且权威。只有 PostgreSQL collector 的 gather error 能成为 Composite gatherer 返回的 fatal error。PgBouncer、Patroni、pgBackRest 或日志指标失败时可以移除自己的数据并更新自己的健康状态，但不能把一份本来合法的 PostgreSQL 响应变成 HTTP 500。

这条规则针对组合端点最危险的故障模式：可选 Patroni 请求的 TLS 错误、缓慢的备份仓库或畸形日志记录，都不能隐藏运维人员诊断事故时最需要的数据库指标。

所有可选组件默认关闭。对应 flag 与 URL 为空时，PG Exporter 不创建 collector、不发请求、不执行命令、不扫描文件、不注册组件健康指标，也不会给旧抓取路径增加协调锁。

## 一个协调层，三种执行模型 {#execution-models}

不同来源的时延和新鲜度契约并不相同，因此不应被塞进同一个通用 adapter：

```text
Prometheus /metrics
        |
        v
Composite coordinator
  |-- PostgreSQL SQL       实时、权威
  |-- PgBouncer SQL        实时、可选
  |-- Patroni HTTP         实时、可选
  |-- pgBackRest snapshot  缓存、可选
  `-- PostgreSQL log       缓存、可选
```

PostgreSQL 保留既有实时 SQL 路径。PgBouncer 同样在每次抓取时运行 SQL，因为查询成本低，而且现有 exporter 语义已经有用。Patroni 实时抓取，因为 role、leader、DCS 与 timeline 状态可能立即变化。

pgBackRest 与 PostgreSQL 日志使用后台 worker 和不可变快照。在 Prometheus 请求中执行备份命令或扫描日志，会让数据库指标可用性依赖磁盘、仓库、parser 与持久化时延。它们的详细契约分别记录在[把 pgBackRest 指标移出抓取路径](/zh/design/cached-pgbackrest-metrics/)和[把 PostgreSQL CSV 日志转成持久指标](/zh/design/postgres-log-metrics/)中。

## 实时工作并发且有界 {#live-timeout}

PgBouncer 与 Patroni 在同一个 sidecar timeout 下并发执行，默认上限为 10 秒。PostgreSQL 与它们并行，但不会被这个可选 deadline 取消，避免 sidecar 预算变成 PostgreSQL 权威查询的新超时。

协调层也不会让重叠的 Prometheus 请求排队等待可选实时工作。若已有一轮完整 Composite scrape 运行中，重叠请求会收集 PostgreSQL、进程指标与无锁缓存快照，并把实时可选工作标记为降级或省略，而不是等待上一轮结束。

这是降级策略，不只是性能优化。抓取风暴发生时，应先降低可选完整性，而不是增加主路径延迟和 goroutine 队列。

## Metric family 所有权 {#family-ownership}

合并多个 registry 必须为同名 family 指定确定性规则。最终顺序是：

```text
PostgreSQL > Patroni > PgBouncer > pgBackRest > PostgreSQL Log
```

进程与 HTTP 自监控也排在 PostgreSQL 之后。低优先级来源只有在高优先级来源未占用 family 名及其 Histogram/Summary 保留派生名时才能加入。即使 Help、类型和标签完全相同，也不能往现有 family 追加样本。

这个整族规则避免两个组件部分共同拥有一个指标，也会阻止高优先级 `foo` Histogram 与低优先级字面 `foo_count` 并存。可选组件中没有冲突的 family 仍可保留；冲突会把该组件标为 `gather` 失败，却不会改变 PostgreSQL 结果。

## Patroni 需要解析，而不是盲透传 {#patroni-semantics}

Patroni 已经提供 Prometheus 指标，但字节拼接会绕过验证：只要输出冲突元数据、OpenMetrics 专用语法、过量数据或重复 family，最终响应就可能非法。Composite collector 因此会抓取、解析、验证，并重新编码受支持的经典 Prometheus 语义。

设计保留 Patroni 的 family 名、Help、类型、标签与 sample value，不给每个业务指标重命名或增加 `component` 标签。来源身份属于 target label 和组件健康面，不应进入所有业务序列。

出站 HTTPS 使用系统 root 加可选 CA 文件。设计不提供 `insecure_skip_verify`；证书错误应成为可见的 Patroni 组件故障，而不是静默削弱传输验证。

## 健康不是一个布尔值 {#health}

每个启用组件都有固定、低基数的健康面：

```text
pg_exporter_component_enabled{component="..."}
pg_exporter_component_up{component="..."}
pg_exporter_component_scrape_duration_seconds{component="..."}
pg_exporter_component_scrape_errors_total{component="...",reason="..."}
pg_exporter_component_last_success_timestamp_seconds{component="..."}
```

这些信号回答不同问题：`enabled` 是配置状态，`up` 是最近一次组件结果，`last_success` 表示陈旧程度，错误 Counter 则保留 connect、timeout、TLS、parse、gather、命令执行、state 或 source 等有限原因。

它们不会替代 PostgreSQL 既有的 `/up`、`/health`、`/primary`、`/replica` 语义。那些路由继续描述 PostgreSQL target；改成“所有组件都健康”会破坏从未选择 Composite 可用性定义的路由与故障转移用户。

`--disable-intro` 只抑制 exporter 与 component 自监控，不抑制业务指标，延续该参数原有含义。

## 被否决的替代方案 {#alternatives}

设计有意拒绝了几种更宽泛的抽象：

- 通用 plugin registry 会在真实组件尚未稳定之前，把生命周期和优先级暴露成公共扩展 API，并增加首轮审计成本。
- 串行采集会让一个可选来源耗尽完整请求预算，后续来源甚至无法开始。
- Patroni 字节透传省掉一次解析，却同时放弃冲突、协议和资源验证。
- 给所有 family 增加 `component` 标签会破坏既有指标契约、扩大序列数，也不能解决名称所有权。
- “所有来源必须成功”会让可选集成降低整体可用性。
- 同一个改动里替换全部独立 exporter 与 Pigsty target，会把源码正确性和部署迁移混在一起并移除回滚选择。

最终设计刻意明确而非通用：具名组件、固定优先级、实时与缓存两条路径，以及 PostgreSQL-first 失败语义。

## 结果与发布门槛 {#consequences}

Composite 模式可以减少 target 与进程数量，同时保留既有 namespace。代价是一个进程要承担更多凭据、网络客户端、parser、后台 worker 与健康状态。运维人员必须只授予已启用组件所需权限，并把 family 冲突视为配置或兼容缺陷。

开发树中已有实现，不等于稳定版、Pigsty target 迁移、Dashboard、recording rule、告警或旧进程退役已经发生。功能进入公开分支和版本时，必须分别验证这些门槛。
