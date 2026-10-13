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

PG Exporter 为 Prometheus 采集 PostgreSQL 与 PgBouncer 指标。本文档对应 **[v{{< param version >}}](https://github.com/pgsty/pg_exporter/releases/tag/v{{< param version >}})**。

## 从这里开始 {#start-here}

- [项目简介](/zh/intro/) — 了解导出器在监控系统中的作用。
- [快速上手](/zh/start/) — 安装导出器并采集第一组指标。
- [下载](/zh/download/) — 选择软件包、程序压缩包或容器镜像。
{.cards}

## 生产运行 {#run-it-in-production}

- [生产部署](/zh/deploy/) — 运行服务并接入 Prometheus。
- [安全指南](/zh/security/) — 配置数据库权限、凭据与 TLS。
- [故障排查](/zh/troubleshooting/) — 诊断连接错误、指标缺失与抓取缓慢。
{.cards}

## 配置导出器 {#understand-and-extend-it}

- [采集器配置](/zh/config/) — 定义 SQL 查询、指标及采集选项。
- [内置采集器](/zh/collectors/) — 查找可用指标及前置条件。
- [命令行参数](/zh/cmd/) — 查询参数、环境变量与默认值。
- [HTTP API](/zh/api/) — 检查健康状态、查看采集结果和重载配置。
- [兼容性](/zh/compatibility/) — 核对数据库版本、平台与架构。
{.cards}

## 开发与发布

- [开发指南](/zh/development/) — 构建导出器、修改采集器并运行测试。
- [设计记录](/zh/design/) — 了解架构决策与未发布功能的设计。
- [发布说明](/zh/release/) — 查看各版本的变更与下载文件。
{.cards}

在 Windows/Linux 上按 {{< kbd "Ctrl" "K" >}}，或在 macOS 上按 {{< kbd "⌘" "K" >}} 打开搜索。

源码与问题反馈位于 [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter)。
