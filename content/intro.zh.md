---
title: "项目简介"
linkTitle: "项目简介"
description: "PG Exporter 如何采集指标，以及如何接入监控系统"
weight: 10
icon: fa-solid fa-lightbulb
categories: [概念]
---

PG Exporter 读取 PostgreSQL 或 PgBouncer 的统计信息，并将其转换为 Prometheus 指标。Prometheus 通过 HTTP 抓取并存储这些指标，用于查询、仪表盘和告警。

每个导出器进程监控一个 PostgreSQL 实例或一个 PgBouncer 实例。同时监控两者时，需要运行两个进程。

## 如何采集指标

一个采集器由一条 SQL 查询及其 YAML 定义组成。YAML 定义告诉导出器如何将查询结果列转换为指标和标签。

首次抓取时，导出器根据目标的版本、主备角色和已安装扩展选择采集器。PostgreSQL 数据库自动发现功能还可以连接同一实例内的其他数据库。

Prometheus 请求 `/metrics` 时，导出器执行选中的查询并返回指标。每个采集器可以缓存一段时间的结果，这段时间称为 TTL。TTL 到期前，后续抓取会复用缓存。

导出器提供 HTTP 指标端点，Prometheus 保存历史数据，Grafana 等仪表盘工具负责展示。

## 可以监控什么

内置采集器覆盖活动会话、复制、WAL、锁、事务、数据库对象及部分扩展，数据来自 PostgreSQL 监控视图和 PgBouncer 管理命令。[内置采集器](/zh/collectors/)列出了指标及所需权限。

导出器也会报告自身状态。例如，`pg_up` 表示主数据库抓取是否完成且没有致命错误，`pg_version` 表示数据库版本，`pg_in_recovery` 表示主备角色。

## 自定义采集

先使用内置配置 [`pg_exporter.yml`](https://github.com/pgsty/pg_exporter/blob/v1.4.1/pg_exporter.yml)，需要更多指标时再添加查询。每个采集器都可以单独设置选择条件、超时与缓存 TTL。

修改配置后，通过 `/reload` 重载。导出器先检查新配置，再替换当前配置，无需重新编译或重启程序。

[采集器配置](/zh/config/)介绍了 YAML 字段及用法示例。

## 检查采集结果

通过 `/explain` 查看主数据库选中的采集器，通过 `/stat` 查看查询次数、报错次数与耗时。[HTTP API](/zh/api/)还提供健康检查和主备角色端点。

遇到连接错误、指标缺失或查询缓慢时，按[故障排查](/zh/troubleshooting/)定位问题。

## 版本与下一步

本文档对应 **v{{< param version >}}**。默认配置包含 PostgreSQL 10–19 和 PgBouncer 1.8–1.25 的采集分支，独立 legacy 配置覆盖 PostgreSQL 9.1–9.6。详情见[兼容性](/zh/compatibility/)。

[设计归档](/zh/design/)介绍了组合数据源、pgBackRest 指标和 PostgreSQL 日志指标等开发功能。这些功能尚未包含在 v{{< param version >}} 中。

首次使用请按[快速上手](/zh/start/)采集指标，部署长期运行的服务请看[生产部署](/zh/deploy/)。
