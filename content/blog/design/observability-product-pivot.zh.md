---
title: "我们最终没有做的 PostgreSQL 可观测性产品"
linkTitle: "可观测性产品转向"
date: "2026-08-13T14:17:01+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "为什么独立事故工作台最终变为 PG Exporter 内的 CSV 日志采集器"
summary: "已于 2026-08-24 被取代。CSV 解析和持久状态要求纳入有限的日志指标功能，独立产品提案终止。"
categories: [design]
tags: [设计, 产品, PostgreSQL, 可观测性]
---

我们最初考虑做一个本地 PostgreSQL 事故工作台：读取结构化日志，重建会话时间线，提供交互过滤与终端界面，后续再作为 Agent 运行。

> **状态：** 已于 2026-08-24 被 [PostgreSQL 日志指标](/zh/design/postgres-log-metrics/)方案取代。<br>
> **决策日期：** 2026-08-13 开始研究；2026-08-24 调整范围。<br>
> **最后核验：** 2026-10-13。<br>
> **范围：** 独立 PostgreSQL 事故工作台与 Agent 提案。<br>
> **交付进度：** 止于提案，未实现、发布或部署。

眼前需求更小：从 PostgreSQL 日志中提取可靠的运维指标。最终选择是在 PG Exporter 中增加后台采集器。本文记录保留的研究结论，以及放弃独立产品的原因。

## 最初提案 {#original-hypothesis}

事故发生时，DBA 可能只有本机日志，没有集中日志服务。理解 PostgreSQL CSV、SQLSTATE、会话与轮转的工具，可以在不上传 SQL 文本的情况下生成时间线。

提案包括：

- PostgreSQL 14+ CSV 解析，包括多行字段；
- 按时间、严重级别、SQLSTATE、数据库、用户、应用和会话过滤；
- 跨重命名日志文件保留上下文；
- 交互式终端界面；
- 本地处理与低基数 Prometheus 指标；
- 后续增加持久游标和多个输出目标的守护进程。

## 保留的结论 {#retained-findings}

PostgreSQL 14 到 18 文档给出了相同的 26 列 CSV 布局。示例导入表以 `(session_id, session_line_num)` 为主键。CSV 字段可包含逗号、引号和换行，因此解析器必须读取完整记录。

SQLSTATE 比本地化消息文本稳定，是错误分类的主要依据。检查点、自动清理、锁等待、临时文件和连接消息，需要针对支持版本和语言测试匹配规则。

原始 SQL、用户名、数据库名、客户端地址和会话标识不适合作为默认指标标签。它们会暴露源数据，并使序列数量随工作负载变化。固定事件类别和有限分布更适合 Prometheus。

轮转、部分写入、重启恢复和游标持久化决定计数是否可靠，必须从一开始就纳入功能契约。

## 调整范围的原因 {#rejected-product}

工作台需要独立的命令、输出结构、界面、软件包、文档和发布周期。Agent 还需要队列、重试、保留策略和服务管理。这些职责超过了指标导出器的范围。

PG Exporter 已有抓取目标、`/metrics`、打包和 Pigsty 集成；开发中的协调层也提供组件健康指标。有限范围的日志采集器可以复用这些能力，满足眼前需求。

因此，我们停止独立产品、仓库和品牌工作，将交互调查与日志发送移出范围。

## 替代方案 {#replacement}

2026-08-24 的决策是：

> 为 PG Exporter 增加默认关闭的 PostgreSQL CSV 日志后台采集器，在现有 `/metrics` 端点发布有限的运维指标。

替代方案保留完整 CSV 解析、文件身份、轮转与截断处理、持久游标与聚合值、原子持久化、不可变快照、固定标签和明确的输入缺口指标。

日志发送、交互查询、会话时间线、任意正则表达式和自动根因分析仍不在范围内。实现契约见 [PostgreSQL 日志指标](/zh/design/postgres-log-metrics/)。

## 何时重新评估 {#why-keep-it}

独立工作台需要一个现有日志工具无法满足的本地调查场景，也需要用户验证事件模型，以及维护者承担发布和支持周期。在这些需求明确之前，PG Exporter 继续提供聚合指标。

## 来源 {#sources}

CSV 要求来自 [PostgreSQL 14](https://www.postgresql.org/docs/14/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) 与 [PostgreSQL 18](https://www.postgresql.org/docs/18/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) 官方日志文档。替代方案的源码边界和测试证据记录在链接的设计文章中。
