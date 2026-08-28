---
title: "我们最终没有做的 PostgreSQL 可观测性产品"
linkTitle: "可观测性产品转向"
date: "2026-08-13T14:17:01+08:00"
lastmod: "2026-08-24T12:17:38+08:00"
authors: [Vonng]
description: "为什么我们探索过 local-first PostgreSQL 事故工作台，最后却把目标收缩为 PG Exporter 内部的 CSV 日志指标"
summary: "已于 2026-08-24 被取代。研究确认了 CSV、持久状态与基数要求，随后否决新工作台、Agent、仓库与品牌，转而在 PG Exporter 内实现有限指标。"
categories: [design]
tags: [设计, 产品, PostgreSQL, 可观测性]
---

> **决策状态：** 2026-08-24 被进程内 PostgreSQL CSV 日志指标方案取代。<br>
> **研究日期：** 2026-08-13。<br>
> **仍然有效：** CSV framing、轮转、SQLSTATE、隐私和有限基数结论。<br>
> **不再适用：** 新产品、仓库、binary、品牌、交互查询工具、TUI、Agent 或日志发送管道。

在收敛 PostgreSQL 日志指标范围之前，我们探索过一个大得多的产品：local-first 事故工作台。它可以检查结构化日志、重建 session 时间线、提供交互过滤与终端界面，并最终演进成节点信号 Agent。

这次探索之所以有价值，恰恰是因为产品没有被做出来。它把任何正确 PostgreSQL 日志 parser 都需要面对的事实，与会改变 PG Exporter 产品类别和运维模型的野心分开了。

## 最初的假设 {#original-hypothesis}

用户问题真实存在。事故发生时，DBA 往往拥有本机 PostgreSQL 日志，却没有在中央平台准备好查询。一个理解 PostgreSQL CSV record、SQLSTATE、session、轮转和多行字段的工具，可以在不上传 SQL 文本、不先部署后端的前提下给出有用时间线。

当时设想的工作台强调：

- 正确解析 PostgreSQL 14+ CSV，而不是使用逐物理行正则；
- 按时间、severity、SQLSTATE、database、user、application 与 session 过滤；
- 跨 rename rotation 保留上下文；
- 在没有 Web 服务的机器上提供 terminal-first 工作流；
- 默认本地处理，保护隐私；
- 从同一 parser 产生低基数 Prometheus 指标；
- 未来可能增加持久游标和多输出的 daemon。

这是一个自洽的产品想法，也远大于眼前需求。

## 研究确认了什么 {#retained-findings}

几项结论在转向后仍然成立。

PostgreSQL 14 到 18 文档给出相同的 26 字段 CSV 布局，其中包含 `session_id`、`session_line_num`、`backend_type`、leader PID 与 query ID。PostgreSQL 的示例导入表使用 `(session_id, session_line_num)` 作为主键。CSV 字段可以包含逗号、引号和换行，因此逐物理行 scanner 不是正确 parser。

SQLSTATE 比本地化 message 文本稳定，是错误分类的第一依据。Message grammar 仍适合 checkpoint、autovacuum、lock wait、temporary file 与连接事件等有限 PostgreSQL 事件，但必须版本化并有测试。

原始 query、detail、hint、context、user、database、application、client address、PID、session、transaction ID 与文件路径都不适合作为默认 metric label。Prometheus 适合有限计数和分布，不是日志索引的替代品。

轮转、部分写入、重启恢复与游标持久化是产品需求，不只是 parser 实现细节。重启后静默重计或漏计的工具，会产生比没有工具更糟的证据。

## 为什么否决更大的产品 {#rejected-product}

决定性问题不是技术可行性，而是范围与责任。

工作台需要独立命令、输出 schema、UX、软件包、文档、支持表面与发布周期。有状态 Agent 还会引入服务管理、升级、队列、背压、重试、磁盘保留、安全政策与发送 SLO。TUI 和日志索引优化人工调查，Prometheus Exporter 优化有限的机器可读状态。把它们放进同一个 MVP，会延迟最小有用结果，也更难证明可靠性。

新产品也没有得到必须独立存在的验证。眼前请求不是“搜索全部日志”或“把日志送到另一个后端”，而是“从 PostgreSQL 结构化日志提取少量可靠运维指标”。PG Exporter 已经拥有这项工作需要的 target identity、`/metrics`、软件包、组件健康与 Pigsty 集成。

品牌和仓库工作因此成为干扰。过早给推测中的产品命名，会让架构显得比用户价值更确定。设计审查最终选择删除整个公开命名表面，而不是继续打磨它。

## 替代决策 {#replacement}

2026-08-24，目标被有意收缩为：

> 在现有 PG Exporter 进程里增加一个默认关闭的 PostgreSQL CSV 后台 collector，只在现有 `/metrics` 上暴露有限的运维指标。

替代方案明确排除日志发送、OTLP、VictoriaLogs、Kafka、Web UI、TUI、全文搜索、session timeline、任意用户正则、自动根因分析和其他组件日志。

它保留真正决定可信度的难题：完整 CSV framing、文件身份、rename 与 truncate、持久游标加累计值、原子持久化、不可变快照、固定标签、序列上限与显式 gap。

最终工程契约见[把 PostgreSQL CSV 日志转成持久指标](/zh/design/postgres-log-metrics/)。

## 为什么保留被取代的记录 {#why-keep-it}

删除探索过程会隐藏这些诱人功能为何缺席；直接发布原始研究同样会误导读者，因为其中包含已经被推翻的命名工作、市场快照与产品建议。

这篇校准后的记录只保留有用因果链：

```text
真实事故工作流
    -> 正确 CSV 与 session 研究
    -> 范围过大的工作台与 Agent 提案
    -> 范围和所有权审查
    -> PG Exporter 内部的有限日志指标
```

未来维护者不应仅因为交互调查听起来有价值就重新打开大产品路线。只有在用户确实需要现有日志栈无法提供的本地查询体验、至少两个真实消费者验证了事件模型，并且有人愿意承担独立产品生命周期时，才值得重新评估。

## 来源 {#sources}

本文保留的稳定外部事实来自 PostgreSQL 自身的 CSV 日志定义：[PostgreSQL 14](https://www.postgresql.org/docs/14/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) 与 [PostgreSQL 18](https://www.postgresql.org/docs/18/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG)。原研究中的产品与品牌快照有意不再转载。
