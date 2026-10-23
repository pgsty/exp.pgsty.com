---
title: "兼容性"
linkTitle: "兼容性"
description: "支持的 PostgreSQL 与 PgBouncer 版本、发布产物、体系结构与部署约束"
weight: 40
icon: fa-solid fa-layer-group
categories: [参考]
---

按运行主机选择安装包，按数据库版本选择采集配置，再安装所需的视图或扩展。本页说明 v{{< param version >}} 随附配置的兼容范围。

## 数据库目标

| 目标 | 状态 | 配置 |
|:---|:---|:---|
| PostgreSQL 10-18 | 默认支持 | `pg_exporter.yml` / `config/` |
| PostgreSQL 19 | 已包含版本专用分支 | 默认配置；在实际服务器构建上检查查询结果 |
| PostgreSQL 9.1-9.6 | Legacy 支持 | `legacy/pg_exporter.yml` / `legacy/config/` |
| PostgreSQL 9.0 及更早版本 | 不支持 | — |
| PgBouncer 1.8+ | 按版本选择采集器 | `0910`-`0940` 采集器文件；连接管理数据库 |
{.full-width}

PostgreSQL 19 分支覆盖恢复、锁、自动清理评分、WAL、订阅、接收器与复制槽。采集器按服务器版本号选择分支；首次抓取后，检查 `/stat`，确认查询与实际服务器构建匹配。

内置 PgBouncer 采集器要求 1.8 或更高版本。1.8 调整了查询所用的 `SHOW STATS` 字段。最新配置分支未设版本上限；升级 PgBouncer 后，结合[上游变更日志](https://www.pgbouncer.org/changelog.html)检查采集结果。

## 发布验证

v1.5.0 候选已以非超级用户通过 PostgreSQL 9.1–9.6、10–18、19 RC1 的默认主库采集，以及 PgBouncer 1.26.1 实测。PG10–13 使用文档要求的订阅 OID 授权；另验证了物理备库晋升、断连恢复及并发采集／健康检查／重载。PG19 证据对应 RC1，不等于覆盖所有正式版构建、扩展与生产负载。

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

发布压缩包包含二进制、合并后的默认配置、许可证、默认环境文件与 systemd 单元。PostgreSQL 9.x 配置需要从对应源码标签获取，不在这些二进制压缩包中。macOS 与 Windows 产物适合开发或连接远端目标；软件包提供的服务集成只适用于 Linux。

> [!NOTE] v1.4.1 起的 RPM 包名
> 官方 RPM 包名与产物前缀改为 `pg-exporter`。新包为旧的 `pg_exporter` 名称声明了 `Provides` 与 `Obsoletes`，因此可以直接升级。可执行文件与配置名仍为 `pg_exporter` 和 `/etc/pg_exporter.yml`。

## 容器约束

官方镜像基于 `scratch` 构建，只包含静态 exporter 二进制、`/etc/pg_exporter.yml` 与许可证；镜像内没有 Shell，也没有操作系统 CA 证书包。使用 `sslmode=verify-ca` 或 `verify-full` 时，需要显式挂载 CA 证书。

## 采集器级前置条件

采集器还会按目标数据库的实际条件选择：

- `primary` / `replica` 标签按恢复角色限制执行。
- `dbname:`、`extension:`、`schema:` 与 `username:` 标签要求对应事实匹配。
- 谓词查询可以执行额外的运行时检查。
- 默认关闭的采集器（`skip: true`）必须显式启用。
- 表/索引膨胀等辅助视图采集器需要相应视图与权限。

先抓取一次 `/metrics`，再通过 [`/explain`](/zh/api/#get-explain) 查看当前采集计划，通过 `/stat` 检查查询结果。每个文件的前置条件参见[内置采集器](/zh/collectors/)。
