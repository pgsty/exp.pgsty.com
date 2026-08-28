---
title: "把 PostgreSQL CSV 日志转成持久指标"
linkTitle: "PostgreSQL 日志指标"
date: "2026-08-24T12:17:38+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
authors: [Vonng]
description: "PG Exporter PostgreSQL CSV 日志指标的产品边界、持久状态协议、有限指标契约与失败语义"
summary: "已实现但未发布。一个默认关闭的 worker 把完整 PostgreSQL CSV record 转成有限持久 Counter 与 Histogram，并在发布不可变快照前先提交游标和聚合状态。"
categories: [design]
tags: [设计, PostgreSQL, 日志, Prometheus, 可靠性]
---

> **决策状态：** 已在开发线实现；截至 2026-08-28，尚未进入 `main`、tag 或公开软件包。<br>
> **决策日期：** 2026-08-24。<br>
> **适用范围：** Composite Exporter 中默认关闭的 PostgreSQL 14+ CSV 日志 collector。<br>
> **取代：** [我们最终没有做的 PostgreSQL 可观测性产品](/zh/design/observability-product-pivot/)中独立产品的方向。<br>
> **发布边界：** 已有实现与源码测试；合并、release、软件包、Pigsty 部署与生产 canary 仍是独立门槛。

PostgreSQL 日志包含 SQL 快照无法重建的运维事实：deadlock、认证失败、被取消的 autovacuum worker、checkpoint 阶段、temporary file 删除、客户端断连，以及由日志策略选择记录的 statement duration。设计问题不在于这些记录是否有用，而在于如何暴露一小组可靠信号，同时不把 PG Exporter 变成日志平台。

最终边界刻意保持狭窄：

> PG Exporter 持续读取一个本地 PostgreSQL CSV 日志目录，持久化有限的聚合状态，并在现有 `/metrics` 上发布低基数 Counter 与 Histogram。它不存储、查询或发送原始日志。

## 产品边界 {#product-boundary}

Collector 属于现有 `pg_exporter` binary、软件包、service、target 与 `/metrics`。只有非空日志目录才会启用：

```bash
pg_exporter \
  --pg-log-dir=/var/log/postgresql \
  --pg-log-state-file=/var/lib/pg_exporter/pglog-state.json \
  --pg-log-poll-interval=1s
```

对应环境变量是 `PG_EXPORTER_PG_LOG_DIR`、`PG_EXPORTER_PG_LOG_STATE_FILE` 与 `PG_EXPORTER_PG_LOG_POLL_INTERVAL`。默认目录为空，默认状态文件为 `/var/lib/pg_exporter/pglog-state.json`，默认轮询间隔为一秒。

关闭时不存在 worker、目录扫描、状态锁、状态文件、日志 metric family 或额外 scrape 协调。`--dry-run` 与 `--explain` 不启动 worker。

功能明确不提供 JSONLOG、stderr、syslog、journald、云日志 API、其他组件日志、日志发送、OTLP、Kafka、VictoriaLogs、Loki、全文搜索、TUI、session timeline、任意用户正则、reset endpoint 或自动根因分析。PostgreSQL logging setting 继续属于普通 SQL/部署配置，不存在 `pg_log_setting_*` 指标。

## 为什么选择 CSV，为什么必须读取完整 record {#csv-contract}

PostgreSQL 14 到 18 文档给出相同的 26 个 CSV 字段，包括 timestamp、user、database、process 与 session identity、per-session line number、severity、SQLSTATE、message 字段、application、backend type、parallel leader PID 与 query ID。PostgreSQL 示例导入表使用 `(session_id, session_line_num)` 作为主键。

CSV 不是一条物理行一个 record。Query、detail、hint 与 context 字段可以包含逗号、引号、回车和嵌入换行。`bufio.Scanner`、`tail -F | regex` 或 `strings.Split` 最终都会把一个逻辑 record 拆成多个假记录。

Collector 使用完整 CSV framing 状态机与标准 CSV decoder。Active file 末尾未完成的 record 会保留为 pending input；只有逻辑 record 完整解析后才提交 offset。单条 record 上限是 16 MiB。畸形或超大数据会进入有限 resync 路径，并增加明确的 parse 与 gap Counter，而不是静默前进并假装没有问题。

第一版只支持 PostgreSQL 14+，以获得固定 26 列 schema。连续 schema mismatch 会让组件降级，不会猜测另一种格式。

## Polling、文件身份与轮转 {#file-semantics}

Worker 周期性 reconcile 目录，而不把 `fsnotify` 当权威。面对 rename rotation、丢失通知、重启和已有多代日志时，polling 更容易实现成可移植、可审计的正确模型。

每个 cursor 记录稳定文件身份、generation、哈希后的路径身份、byte offset、size、小型内容 fingerprint、EOF/消失状态和 resync 状态。持久文件不保存明文日志路径。

Rename rotation 按 identity 跟随：旧文件改名后仍可读完，新文件使用自己的 cursor 开始。如果文件小于已提交 offset，collector 将其视为 truncate，把该 generation 的 offset 重置为零，并同时增加 rotation 与 input-gap 指标。Copy-truncate 可能在 reader 发现之前覆盖未读字节，因此设计报告不可避免的 gap，而不承诺不可能实现的 exactly-once。

未读完的文件消失和 fingerprint identity change 也会成为显式 gap。已经读完且消失的 cursor 可以作为 tombstone 淘汰。状态最多跟踪 256 个文件 identity，不会为了满足上限而删除仍有活动工作的 cursor。

首次启动且没有状态文件时，所有现有文件在当前 EOF 建立 baseline，避免把任意保留历史当成新 Counter。Baseline 会增加 `state_resets_total` 与一个 input-gap 原因，让运维人员看见指标进入了新 epoch。第一版不提供历史回填。

## 持久提交协议 {#durable-commit}

从日志派生的 Counter 与 Histogram 必须跨 PG Exporter 重启保存。只推进 cursor 而不保存聚合会漏计；只发布聚合而没有匹配 cursor，重启后会重复计数。设计把它们放进同一个版本化状态对象提交。

一轮后台周期遵循以下顺序：

```text
扫描并读取完整 record
    -> clone 上一版 state
    -> 更新 cursor、counter、histogram 与 self-state
    -> 验证单调性、标签、上限与 metric family
    -> 写入 0600 临时状态文件
    -> fsync 临时文件
    -> 原子 rename
    -> 在支持的平台 fsync 父目录
    -> 发布与之匹配的不可变指标快照
```

状态文件上限为 4 MiB，必须是权限 `0600` 的普通文件；symlink 与不安全权限会被拒绝。非阻塞状态锁阻止两个进程共同拥有同一游标。状态中的目录身份必须与配置来源一致。

发布点至关重要。Rename 前崩溃会保留旧 state 与旧 snapshot；rename 后、下一次 scrape 前崩溃会留下新 durable state，重启后可恢复相同 family。请求路径只读 atomic pointer，永远不扫描文件、不解析 CSV、不写状态、不调用 `fsync`。

每轮 pass 最多处理 100,000 条 record 或 64 MiB。若仍有 backlog，worker 会立即继续下一轮，而不是等待普通 poll interval。

## 指标与基数 {#metric-contract}

核心 family 是：

```text
pg_log_records_total{severity}
pg_log_errors_total{severity,sqlstate_class}
pg_log_query_duration_seconds{kind}
pg_log_events_total{category,event}
```

常规默认表面还覆盖有限 exact SQLSTATE、checkpoint/restartpoint 数量与 duration/WAL 活动、autovacuum 结果与 duration、lock wait、temporary file 数量与大小、连接和 session duration。

与 SQL [快照直方图](/zh/design/snapshot-histograms/)不同，日志 Histogram 是持久累计观测。它的 bucket、count 与 sum 连同 cursor 一起持久化，所以在显式 state reset 形成可见新 epoch 之前，普通 Prometheus Counter Histogram 的 `rate()` 等查询适用。

标签全部来自固定枚举。例如 query duration 的 `kind` 只有 `statement`、`execute`、`parse`、`bind`、`other`。Exact SQLSTATE 仅允许官方 code，最多 128 个已观察 code 序列，custom 与 unknown 合并为 `other`。完整日志指标表面有 1,200 序列硬上限。

原始 query、message、detail、hint、context、database、user、application、relation、query ID、client address、PID、session、transaction ID 与文件路径永远不进入 label 或 durable state。一条 record 可以贡献多个安全聚合，但最多只产生一个 primary classified event。

这些决策用取证细节换取可预测监控。Exporter 能告警 deadlock 或认证失败增加，却无法展示触发它们的 SQL 文本。

## 自监控与可信度 {#self-observability}

没有 reader 健康证据，业务指标本身并不可信。Collector 增加：

```text
pg_exporter_log_bytes_read_total
pg_exporter_log_parse_errors_total{reason}
pg_exporter_log_files_watched
pg_exporter_log_last_record_timestamp_seconds
pg_exporter_log_state_persist_timestamp_seconds
pg_exporter_log_rotations_total{type}
pg_exporter_log_input_gaps_total{reason}
pg_exporter_log_state_resets_total
```

它还以 `pg_exporter_component_*{component="postgres_log"}` 进入统一健康面。输入、权限、parser、state、limit 或 family conflict 故障只会把日志组件标为 down。在安全的情况下，上一份已提交业务快照继续可用；`up`、最后成功时间与错误 Counter 会显示它已经陈旧或不完整。

`--disable-intro` 移除 exporter/component/log-reader 自监控，但保留 `pg_log_*` 业务指标，延续 exporter introspection 与领域数据的既有边界。

## 日志策略决定指标含义 {#logging-policy}

Collector 只能测量 PostgreSQL 选择输出的 record。因此 `pg_log_query_duration_seconds` 是由 `log_duration`、`log_min_duration_statement`、采样与协议行为决定的条件分布。除非 PostgreSQL 确实配置为记录所有 query duration，否则不能把它描述成全部查询的全局分布。

Checkpoint、autovacuum、connection、disconnection、lock-wait 与 temporary-file family 同样只有在相应服务器设置产生消息时才有数据。PG Exporter 记录这些输入前提，但不把 setting 重复成日志派生指标。

PostgreSQL 日志可能包含敏感 statement 和客户端数据。Service account 需要读取指定目录，但不能把日志改成 world-readable。Collector 只保存有限聚合与哈希 source identity，不会把原始 record 复制进状态文件。

## 被否决的方案 {#alternatives}

- 在 `/metrics` 中读取日志被否决，因为解析与持久化时延会进入 PostgreSQL 抓取路径。
- `fsnotify` 不能作为正确性权威，因为通知可能丢失，也不能替代重启后的 reconcile。
- 首次启动处理全部历史文件被否决，因为 retention policy 会不可预测地定义 Counter 起点。
- At-least-once 发布被否决，因为重复告警 Counter 不是可接受的恢复策略。
- 动态标签和用户正则被否决，因为输入数据会控制基数与持久 schema。
- 新 endpoint 或 binary 被否决，因为这是一个有限 metric source，不是第二个产品。

## 验收与剩余门槛 {#acceptance}

源码验收覆盖 PostgreSQL 14、16、18 fixture；quoted comma、quote、CRLF、multiline 与 partial record；rename rotation、truncate、重启恢复、state lock 与权限；状态持久化前后的 crash point；事件目录 fixture；序列预算；family conflict；关闭快路径；overlap scrape；shutdown；race test 与软件包元数据。

这些测试只能建立实现 candidate，不能证明公开版本。交付前，精确合并提交必须通过仓库 CI 与 package build，再用最终 service user 在 disposable PostgreSQL 实例上验证真实轮转和重启。Pigsty target、Dashboard、recording rule、告警、软件包升级与生产 canary 都需要独立证据。

Composite 协调契约见[一个端点，多种来源](/zh/design/composite-exporter/)。CSV schema 与日志输入前提以 PostgreSQL 官方文档为准：[PostgreSQL 14 logging](https://www.postgresql.org/docs/14/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) 与 [PostgreSQL 18 logging](https://www.postgresql.org/docs/18/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG)。
