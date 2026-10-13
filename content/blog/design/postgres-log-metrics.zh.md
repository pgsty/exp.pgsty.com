---
title: "把 PostgreSQL CSV 日志转成持久指标"
linkTitle: "PostgreSQL 日志指标"
date: "2026-08-24T12:17:38+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "读取完整 CSV 记录，持久化游标与聚合值，发布有界 PostgreSQL 日志指标"
summary: "已实现，未发布。默认关闭的后台任务先保存 CSV 游标与聚合值，再发布累计日志指标。"
categories: [design]
tags: [设计, PostgreSQL, 日志, Prometheus, 可靠性]
---

PostgreSQL 日志会记录 SQL 快照可能错过的事件：死锁、认证失败、自动清理取消、检查点、临时文件删除和客户端断连。根据服务端日志策略，还可以记录语句耗时。

> **状态：** 已实现，未发布。<br>
> **决策日期：** 2026-08-24。<br>
> **最后核验：** 2026-10-13。<br>
> **范围：** 源码提交 `c0ba58a` 的 PostgreSQL 14+ CSV 日志采集器，默认关闭；稳定版 `v1.4.1` 尚未包含。<br>
> **取代：** [独立可观测性产品提案](/zh/design/observability-product-pivot/)。<br>
> **交付进度：** 本地测试通过；未合入 `main` 或发布标签；软件包、部署与生产运行未核验。

本采集器读取一个本地 CSV 日志目录，保存有限的聚合状态，并在 `/metrics` 暴露 Counter 和 Histogram。原始日志保留在 PostgreSQL 日志文件中。

## 范围与启用方式 {#product-boundary}

采集器运行在现有 PG Exporter 进程中。指定非空日志目录即可启用：

```bash
pg_exporter \
  --pg-log-dir=/var/log/postgresql \
  --pg-log-state-file=/var/lib/pg_exporter/pglog-state.json \
  --pg-log-poll-interval=1s
```

对应环境变量为 `PG_EXPORTER_PG_LOG_DIR`、`PG_EXPORTER_PG_LOG_STATE_FILE` 和 `PG_EXPORTER_PG_LOG_POLL_INTERVAL`。默认目录为空，状态路径如上，轮询间隔为一秒。

关闭时不创建后台任务、状态锁、状态文件或日志指标，也不增加文件扫描或抓取协调。`--dry-run` 与 `--explain` 不启动后台任务。

范围限于本地 PostgreSQL CSV 日志和聚合指标，不包括其他格式、日志发送、查询界面、会话时间线、任意正则表达式或自动根因分析。日志设置仍由 PostgreSQL 配置管理，采集器不提供 `pg_log_setting_*` 指标。

## 读取完整 CSV 记录 {#csv-contract}

PostgreSQL 14 到 18 文档采用相同的 26 列 CSV 布局，包含时间戳、进程和会话标识、严重级别、SQLSTATE、消息、应用、后端类型、并行主进程 PID 与查询 ID。

字段可以包含逗号、引号、回车和换行，因此读取器先识别完整 CSV 记录，再解码。逐物理行扫描无法正确处理该格式。

文件末尾尚未写完的记录保持待处理，完整后才提交其偏移量。单条记录上限为 16 MiB。畸形或超大输入触发有界重新同步，并增加解析错误和输入缺口计数。连续结构不匹配会使组件保持不可用，直到恢复有效输入。

## 文件身份与轮转 {#file-semantics}

后台任务轮询并核对目录。仅靠文件通知无法恢复遗漏事件，也无法在重启后重建状态。

每个游标保存文件身份、代次、路径哈希、字节偏移、大小、内容指纹和读取状态。状态文件不保存明文日志路径。

重命名轮转按文件身份跟踪：读取器继续读完旧文件，为新文件建立游标。文件大小低于已提交偏移时，视为截断，从零开始新代次，并记录轮转和输入缺口。复制后截断可能在轮询发现前丢弃未读字节，采集器无法恢复这些字节。

未读完的文件消失或内容指纹变化，也会记录缺口。已读完且消失的游标可以移除。状态最多跟踪 256 个文件身份，并保留仍有未读内容的游标。

无状态文件的首次启动，从各现有文件的当前末尾开始读取，同时增加状态重置和输入缺口计数，标明新的计数起点。本设计不回填历史日志。

## 先提交状态，再发布指标 {#durable-commit}

日志 Counter 与 Histogram 必须在 Exporter 重启后保留。游标偏移和聚合值共同提交；只推进其中一个，会导致观测丢失或重复。

一轮后台周期准备候选状态，然后执行：

```text
读取完整记录，更新候选状态
    -> 验证计数器、直方图、标签和上限
    -> 构造并验证指标族
    -> 写入 0600 临时状态文件
    -> fsync 文件
    -> 原子重命名到状态路径
    -> 在支持的平台 fsync 父目录
    -> 发布对应的不可变指标快照
```

状态文件上限为 4 MiB。在 Unix 上，必须是权限 `0600` 的普通文件；符号链接和不安全权限会被拒绝。非阻塞状态锁防止两个进程共用同一状态，保存的目录身份必须与配置来源一致。

重命名前崩溃会留下上一份已提交状态。重命名后崩溃，重启可以恢复新状态并重建对应指标。`/metrics` 只读取已发布快照，不扫描文件、解析 CSV 或写状态。

每轮最多处理 100,000 条记录或 64 MiB。仍有输入时，立即开始下一轮。

## 指标与序列上限 {#metric-contract}

核心指标族为：

```text
pg_log_records_total{severity}
pg_log_errors_total{severity,sqlstate_class}
pg_log_query_duration_seconds{kind}
pg_log_events_total{category,event}
```

其他指标覆盖具体 SQLSTATE 代码、检查点与重启点、自动清理、锁等待、临时文件、连接和会话时长。

日志 Histogram 是与游标一同持久化的累计观测，可使用 `rate()` 等普通 Counter Histogram 查询。显式状态重置会开始新的计数周期。这与描述当前总体、使用 Gauge 序列的 SQL [快照直方图](/zh/design/snapshot-histograms/)不同。

标签采用固定取值。查询时长的 `kind` 只有 `statement`、`execute`、`parse`、`bind` 和 `other`。具体 SQLSTATE 指标仅接受官方代码，最多保存 128 个已观察代码序列，自定义和未知代码归入 `other`。总输出上限为 1,200 条序列。

原始 SQL、消息、数据库名、用户名、应用名、关系名、查询 ID、地址、进程与会话 ID、事务 ID 和文件路径都不进入标签或持久状态。一条记录可以更新多个聚合值，但最多产生一个主要分类事件。例如，指标可以显示死锁增加，而不保留相关 SQL 文本。

## 读取器健康 {#self-observability}

读取器暴露以下指标：

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

它还使用 `pg_exporter_component_*{component="postgres_log"}`。输入、权限、解析、状态、上限或指标族冲突错误只将日志组件标为不可用，最后提交的快照继续提供。结合健康、最后成功时间和缺口计数判断数据的新鲜度与完整性。

`--disable-intro` 移除 Exporter、组件和读取器自监控，保留 `pg_log_*` 业务指标。

## 日志策略决定覆盖范围 {#logging-policy}

指标只覆盖 PostgreSQL 实际输出的记录。查询时长分布取决于 `log_duration`、`log_min_duration_statement`、采样和协议行为。例如，慢语句阈值产生的是已记录慢语句的分布，而非全部查询的分布。

检查点、自动清理、连接、断连、锁等待和临时文件指标也需要对应服务端日志设置。基于消息文本的事件解析依赖支持的语言和格式；基于 SQLSTATE 的错误分类不依赖本地化措辞。

为服务用户授予指定日志的读取权限和状态目录的写入权限。源日志可能包含 SQL 与客户端数据，应限制访问范围。

## 备选方案与非目标 {#alternatives}

- 在 `/metrics` 中读取日志，会给数据库抓取增加解析和持久化耗时。后台任务将这些工作分开。
- 文件通知可以加快发现，但不能替代保证正确性所需的轮询与核对。
- 首次启动重放全部历史文件，会让初始计数取决于日志保留策略。从文件末尾开始可明确建立基线。
- 持久化前发布指标可能导致崩溃后重复计数，因此先提交状态。
- 动态标签与用户匹配规则会使序列数量和保存结构取决于输入，因此采用固定指标目录。
- 独立端点或可执行文件会为同一有限数据源增加部署单元，因此复用现有进程和端点。

## 核验与剩余工作 {#acceptance}

实现位于 `exporter/postgres_log*.go`。测试覆盖 PostgreSQL 14、16、18 样例；引号与多行字段；未完成记录；重命名与截断；重启、锁和权限；崩溃位置；事件分类；序列上限；冲突；重叠抓取与关闭。

外部 CSV 集成测试待核验。设置 `PG_EXPORTER_TEST_PG_LOG_DIR`，使用预定服务用户验证真实日志的轮转与重启恢复。

协调规则见 [Composite Exporter](/zh/design/composite-exporter/)。CSV 定义和日志设置见 [PostgreSQL 14](https://www.postgresql.org/docs/14/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) 与 [PostgreSQL 18](https://www.postgresql.org/docs/18/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) 官方文档。
