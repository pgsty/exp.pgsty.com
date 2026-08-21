---
title: "PG Exporter 文档"
linkTitle: "文档"
description: "安装、部署、加固、运维与扩展 pg_exporter。"
weight: 1
type: docs
icon: fa-solid fa-book
toc_root: true
search_keywords: [pg_exporter, PostgreSQL 监控, PgBouncer, Prometheus, 指标导出器, 文档]
search_boost: 1.6
---

**PG Exporter** 是一款面向 Prometheus 兼容监控系统的高级 PostgreSQL 与 PgBouncer 指标导出器。它将内置的可用性/角色指标与声明式 SQL 采集器引擎组合起来，让指标面可以独立于 Go 二进制持续演进。

本文档以最新稳定版本 **[v{{< param version >}}](https://github.com/pgsty/pg_exporter/releases/tag/v{{< param version >}})** 为基线，作为独立的中英文手册维护；内容比原先 Pigsty 模块中的汇总页更加完整。

## 从这里开始 {#start-here}

- [项目简介](/zh/intro/) — 理解架构、执行模型与产品边界。
- [快速上手](/zh/start/) — 用约五分钟得到可用的 exporter 与 Prometheus 抓取目标。
- [下载](/zh/download/) — 选择、安装、启用并验证软件包、压缩包、容器、Pigsty 或源码构建。
- [安装指南](/zh/install/) — 查阅完整的软件仓库与发布产物参考。
- [兼容性](/zh/compatibility/) — 核对 PostgreSQL、PgBouncer、操作系统、CPU、软件包与容器支持。
{.cards}

## 生产运行 {#run-it-in-production}

- [生产部署](/zh/deploy/) — 参数、环境变量、systemd、Docker、Kubernetes、自动发现、抓取与告警。
- [安全指南](/zh/security/) — 数据库最小权限、密钥、TLS、HTTP 认证与网络暴露面。
- [故障排查](/zh/troubleshooting/) — 以症状为入口，使用日志、`/up`、`/explain`、`/stat` 与配置校验定位问题。
{.cards}

## 理解与扩展 {#understand-and-extend-it}

- [采集器配置](/zh/config/) — 完整 YAML 模型：查询、标签、谓词、TTL、超时、Label、Counter、Gauge 与快照直方图。
- [内置采集器](/zh/collectors/) — 58 个定义文件、采集器分组、前置条件、开销与基数控制。
- [HTTP API](/zh/api/) — 指标、健康检查、角色路由、重载、解释、统计、版本与首页端点。
- [开发指南](/zh/development/) — 构建、测试、修改采集器、重建合并配置与发布产物。
- [发布注记](/zh/release/) — 每个标签版本一篇中英文文章，按时间倒序排列。
{.cards}

## 文档口径

- 命令与路径均对照当前 `pg_exporter` 源码和 v{{< param version >}} 发布产物核验。
- 默认描述稳定版本行为；涉及尚未发布的 `main` 分支行为时会明确标注。
- 已包含 PostgreSQL 19 采集器分支，但目标是否适合生产仍以 PostgreSQL 官方发布状态为准。
- 英文与简体中文页面成对维护，可以通过语言切换器在对应页面之间切换。

在 Windows/Linux 上按 {{< kbd "Ctrl" "K" >}}，或在 macOS 上按 {{< kbd "⌘" "K" >}}，可以从任意页面打开命令面板。输入 `>` 可直接浏览站点与页面命令，无需加载搜索索引。“在 ChatGPT 中打开”与“在 Claude 中打开”属于可选的外部跳转；启用后，当前页面的完整 URL（包括查询参数与片段）会发送给相应服务。

源码、Issue 与贡献入口请访问 [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter)。
