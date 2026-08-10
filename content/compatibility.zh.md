---
title: "兼容性"
linkTitle: "兼容性"
description: "支持的 PostgreSQL 与 PgBouncer 版本、发布产物、体系结构与部署约束"
weight: 40
icon: fa-solid fa-layer-group
categories: [参考]
---

兼容性分为三个独立层面：exporter 二进制必须能在宿主机运行，动态规划必须能为目标服务器选出匹配的采集器分支，可选 SQL 对象或扩展还必须真实存在。因此，“进程能够启动”不等于所有采集器都满足准入条件。

## 数据库目标

| 目标 | 状态 | 配置 |
|:---|:---|:---|
| PostgreSQL 10-18 | 默认支持 | `pg_exporter.yml` / `config/` |
| PostgreSQL 19 | 已包含采集器分支 | 默认配置；需要针对当前预发布/正式服务器构建进行验证 |
| PostgreSQL 9.1-9.6 | Legacy 支持 | `legacy/pg_exporter.yml` / `legacy/config/` |
| PostgreSQL 9.0 及更早版本 | 不支持 | — |
| PgBouncer 1.8-1.25+ | 支持 | `0910`-`0940` 采集器文件；连接管理数据库 |
{.full-width}

PostgreSQL 19 专用分支覆盖新的恢复、锁、自动清理评分、WAL、订阅、接收器与复制槽字段。截至 2026 年 8 月，PostgreSQL 19 仍处于 Beta；PostgreSQL 官方明确说明 Beta 构建用于测试而非生产。部署 PG19 目标前请检查[当前 PostgreSQL Beta 状态](https://www.postgresql.org/developer/beta/)。

PgBouncer 支持从 1.8 开始，因为该版本线具备采集器依赖的管理端 `SHOW` 接口。版本分支目前覆盖到 1.25 系列；上游版本状态以 [PgBouncer Changelog](https://www.pgbouncer.org/changelog.html) 为准。

## v{{< param version >}} 发布产物

| 产物 | 操作系统 | 体系结构 |
|:---|:---|:---|
| Tarball | Linux | amd64、arm64、ppc64le |
| Tarball | macOS | amd64、arm64 |
| Tarball | Windows | amd64 |
| RPM | RHEL 兼容 Linux | x86_64、aarch64、ppc64le |
| DEB | Debian/Ubuntu 兼容 Linux | amd64、arm64、ppc64le |
| Docker 镜像 | Linux 容器 | amd64、arm64 |
{.full-width}

发布压缩包包含二进制、合并配置、许可证、默认环境文件与 systemd 单元。macOS 与 Windows 产物适合开发或连接远端目标；软件包提供的服务集成只适用于 Linux。

{{% alert title="v1.4.1 起的 RPM 包名" color="info" %}}
官方 RPM 包名与产物前缀改为 `pg-exporter`。新包为旧的 `pg_exporter` 名称声明了 `Provides` 与 `Obsoletes`，因此可以直接升级。可执行文件与配置名仍为 `pg_exporter` 和 `/etc/pg_exporter.yml`。
{{% /alert %}}

## 容器约束

官方镜像基于 `scratch` 构建，只包含静态 exporter 二进制、`/etc/pg_exporter.yml` 与许可证；镜像内没有 Shell，也没有操作系统 CA 证书包。使用 `sslmode=verify-ca` 或 `verify-full` 时，需要显式挂载 CA 证书。

## 采集器级前置条件

即使服务器版本受支持，部分采集器仍有更窄的准入条件：

- `primary` / `replica` 标签按恢复角色限制执行。
- `dbname:`、`extension:`、`schema:` 与 `username:` 标签要求对应事实匹配。
- 谓词查询可以执行额外的运行时检查。
- 默认关闭的采集器（`skip: true`）必须显式启用。
- 表/索引膨胀等辅助视图采集器需要相应视图与权限。

请在真实目标上通过 [`/explain`](/zh/api/#get-explain) 查看精确规划结果；每个文件的前置条件参见[内置采集器](/zh/collectors/)。
