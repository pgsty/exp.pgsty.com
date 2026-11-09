---
title: "保留集群进度与准确的关系标识"
linkTitle: "进度指标的数据库范围"
date: "2026-11-09T00:00:00+08:00"
lastmod: "2026-11-09T00:00:00+08:00"
authors: [Vonng]
categories: [design]
tags: [Design, PostgreSQL, Compatibility]
summary: "v1.6.0：保留集群级进度采集，其他数据库的用户关系使用数字 OID。"
---

> **状态：** 已随 v1.6.0 发布。<br>
> **决策／最后核验：** 2026-11-09。<br>
> **范围：** main 上的 v1.6.0，源码 `6bee809`，解决 [#115](https://github.com/pgsty/pg_exporter/issues/115)，涵盖 PostgreSQL 12+ 的 vacuum、建索引与 cluster 进度，未随 v1.5.0 发布。<br>
> **交付：** v1.6.0 标签指向 `6bee809`；GitHub Release、带版本号的压缩包、RPM／DEB 和校验和已发布。源码 CI、制品验收与 amd64／arm64 容器 TLS 验证通过。软件发布不等于生产部署或生产负载验证。

## 决策 {#decision}

进度视图报告整个实例的任务，但 `relid::regclass` 只能在当前连接数据库中解析名称。其他数据库的 OID 可能被解析成不相关的本地关系。

保留 `pg_vacuuming`、`pg_indexing` 与 `pg_clustering` 的 `cluster, primary` 标签。记录属于当前连接数据库，或关系是系统目录时，用 `relid::regclass::text` 解析 `relname`：小于 16384（`FirstNormalObjectId`）的 OID 由 initdb 分配，在每个数据库中都指向同一系统目录。其他数据库的其余关系直接使用数字 OID 文本，并保留 `datname` 与 `pid` 标识任务。不滤除跨库记录。

保留指标名称、标签、类型、版本范围、TTL，以及每次刷新三条集群级查询。关闭自动发现、排除数据库或监控角色无法连接某库时，仍按进度视图原有的可见性规则覆盖跨库任务，不新增连接或名称查询。

## 权衡与未采用方案 {#tradeoff-and-rejected-alternatives}

数字 OID 可读性不如关系名，但准确表达了主连接能够获取的标识。本次解决错误表名，且不丢失系统目录名称（例如其他库中 `pg_attribute` 的 VACUUM），明确不承诺用户关系的跨库名称解析。

放弃逐库采集：它把每次刷新的查询数从三条增加为每库三条，即使没有进度任务也要执行，同时会丢失被排除或无法连接数据库的进度。额外为活跃任务创建名称查询连接会重复自动发现及权限处理；重命名标签则需要单独的指标迁移。基础备份进度保持不变。

## 验收与升级 {#acceptance-and-upgrade}

执行 PostgreSQL 12–16、17、18+ 的 SQL 分支，用相同关系 OID 构造本地与外库记录，验证本地名称、外库数字 OID、外库系统目录名称及每个任务唯一的样本。检查主／备角色计划、发现连接不重复执行集群采集器，并确认关闭自动发现或排除数据库时仍有跨库进度。

同时更新分片 YAML 和生成配置。现有安装需要合并或替换这些定义，仅升级二进制不会应用 SQL 修正。本地 SQL 测试不代表生产负载验收。

## 本地验证 {#local-verification}

PostgreSQL 12、17、18 以监控角色通过 SQL 集成测试，覆盖三组查询版本分支。临时进度视图中，本地与外库任务使用相同关系 OID，本地任务输出名称，外库任务输出数字 OID。PostgreSQL 18 的真实建索引任务在关闭发现、数据库被排除，以及监控角色缺少该库 CONNECT 权限时均保持可见，每个指标只出现一次。计划测试覆盖 PostgreSQL 12–19，防止发现连接重复执行集群采集器。

评审跟进在测试数据中加入外库 `pg_catalog.pg_attribute` 记录。PostgreSQL 18.6 上输出 `pg_attribute`，此前的条件输出 `1249`。对其他库中 `pg_attribute` 的限速 VACUUM 实测结果相同，而该库用户表仍输出 OID。此次跟进未重跑 PostgreSQL 12 与 17。
