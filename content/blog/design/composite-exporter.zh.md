---
title: "一个端点，多种来源：Composite Exporter 契约"
linkTitle: "Composite Exporter"
date: "2026-08-11T23:50:55+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "通过固定所有权和独立故障处理，合并 PostgreSQL 与可选来源的指标"
summary: "已实现，未发布。PostgreSQL 保持主导；实时来源共用超时，缓存来源提供不可变快照。"
categories: [design]
tags: [设计, 架构, Prometheus, PgBouncer, Patroni]
---

Composite 模式把 PostgreSQL、PgBouncer、Patroni、pgBackRest 和 PostgreSQL 日志指标合并到同一个 `/metrics` 端点，减少数据库节点上的进程和抓取目标。PostgreSQL 是主数据源；各可选来源独立报告故障和健康状态。

> **状态：** 已实现，未发布。<br>
> **决策日期：** 2026-08-11；2026-08-23 与 2026-08-24 增加缓存组件。<br>
> **最后核验：** 2026-10-13。<br>
> **范围：** 源码提交 `c0ba58a` 的 Composite 协调层；稳定版 `v1.4.1` 尚未包含。<br>
> **交付进度：** 本地测试通过；未合入 `main` 或发布标签；软件包、部署与生产运行未核验。

## PostgreSQL 保持主导 {#primary-invariant}

只有 PostgreSQL 的指标汇总错误会使 Composite 汇总失败。可选组件故障只影响自身指标和健康状态。只要 PostgreSQL 汇总成功，端点仍返回 HTTP 200。

所有可选组件默认关闭。全部关闭时，启动过程不创建可选后台任务、客户端或文件读取器，抓取路径也不增加 Composite 协调锁。

## 实时采集与缓存快照 {#execution-models}

```text
Prometheus /metrics
        |
        v
Composite 协调层
  |-- PostgreSQL SQL       实时、主数据源
  |-- PgBouncer SQL        实时、可选
  |-- Patroni HTTP         实时、可选
  |-- pgBackRest 快照      缓存、可选
  `-- PostgreSQL 日志      缓存、可选
```

PostgreSQL 与 PgBouncer 使用现有 SQL 采集器及查询缓存。Patroni 的角色和主节点状态变化较快，因此在每次完整抓取中请求其指标端点。

pgBackRest 与 PostgreSQL 日志由后台任务采集，并发布不可变快照。HTTP 请求只读取快照，命令执行、日志解析和状态持久化不会拖慢数据库采集。刷新与恢复规则见[缓存 pgBackRest 指标](/zh/design/cached-pgbackrest-metrics/)和[持久 PostgreSQL 日志指标](/zh/design/postgres-log-metrics/)。

## 超时与并发请求 {#live-timeout}

PgBouncer 与 Patroni 在 `--scrape-timeout` 限制下并发执行，默认 10 秒。PostgreSQL 同时采集，沿用自身查询超时；可选组件的超时不会取消 PostgreSQL 采集。

若已有一轮完整 Composite 抓取正在运行，重叠请求只采集 PostgreSQL、进程指标和缓存快照。它跳过 PgBouncer 与 Patroni 的实时采集，并在本次响应中将这两个组件的 `up` 设为零，不更新已保存的错误计数和最后成功时间。这样可选采集不会形成请求队列。

## 指标族所有权 {#family-ownership}

业务指标的优先级如下：

```text
PostgreSQL > Patroni > PgBouncer > pgBackRest > PostgreSQL Log
```

进程与 HTTP 自监控在 PostgreSQL 之后、可选来源之前合并。组件健康指标最后合并。

先占用名称的来源拥有整个指标族。即使类型、说明和标签一致，低优先级来源也不能追加样本。Histogram 与 Summary 的派生名称同样保留：高优先级 `foo` Histogram 会阻止低优先级 `foo_count` 指标族加入。

发生冲突时，省略冲突指标族，并将可选组件标记为 `gather` 错误。该组件的其他合法指标族仍可保留。

## Patroni 指标接入 {#patroni-semantics}

PG Exporter 抓取、解析、验证并重新编码 Patroni 的经典 Prometheus 文本，保留指标族名称、说明、类型、标签和值，不为业务指标添加 `component` 标签。

响应上限为 1 MiB、10,000 行样本和 256 个指标族。HTTPS 使用系统信任根及可选的 `--http-ca-file`。证书错误会将 Patroni 标记为不可用；没有跳过证书验证的参数。

## 组件健康 {#health}

除非设置 `--disable-intro`，Composite 模式会暴露以下自监控指标：

```text
pg_exporter_component_enabled{component="..."}
pg_exporter_component_up{component="..."}
pg_exporter_component_scrape_duration_seconds{component="..."}
pg_exporter_component_scrape_errors_total{component="...",reason="..."}
pg_exporter_component_last_success_timestamp_seconds{component="..."}
```

`enabled` 表示组件是否启用，关闭的组件为零。`up` 表示采集结果。耗时和最后成功时间对实时来源表示抓取，对缓存来源表示后台周期。错误原因使用固定枚举，例如 `connect`、`timeout`、`tls`、`parse` 和 `gather`。

既有 `/up`、`/health`、`/primary` 和 `/replica` 端点继续描述 PostgreSQL。这些端点用于数据库健康检查与路由，可选组件不改变其含义。`--disable-intro` 移除自监控指标，保留业务指标。

## 备选方案与非目标 {#alternatives}

- 独立 Exporter 提供进程隔离，但需要独立的目标、软件包和服务配置。Composite 是一种可选部署方式。
- 串行采集使总耗时依赖来源顺序。并发实时采集共用一个可选组件超时。
- 原样转发 Patroni 文本无法检查指标所有权和响应上限。解析后可以同时检查两者。
- 通用插件注册机制会在集成尚未稳定时暴露生命周期和优先级规则。本设计采用具名组件和固定优先级。
- 要求所有来源成功，会让数据库监控依赖可选服务。协调层将故障限制在所属组件内。

本设计不改变指标命名空间，也不负责迁移 Pigsty 目标、仪表盘、告警或现有独立 Exporter。

## 核验与运维影响 {#consequences}

实现位于 `exporter/composite.go`、`exporter/patroni.go` 及启动、重载路径。测试覆盖关闭行为、超时、TLS 与格式错误、指标族冲突、并发请求、重载和关闭。

同一个进程需要所有已启用来源的权限，只授予实际所需权限。替换独立 Exporter 前，在目标环境验证正式软件包、目标标签、仪表盘和告警。
