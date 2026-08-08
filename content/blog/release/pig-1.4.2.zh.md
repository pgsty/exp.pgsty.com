---
title: "pig v1.4.2"
linkTitle: "v1.4.2"
date: 2026-06-18
author: "冯若航"
description: "524 个扩展，PG19 beta，pgrx 0.18.1，Patroni 修复"
categories: [release]
tags: [Release, pig]
weight: 50
---

- 内置扩展目录从 **510** 个可用扩展刷新到 **524** 个，新增 14 个扩展：`pg_stl`、`pgmnemo`、`psql_bm25s`、`pg_orca`、`pg_sorted_heap`、`graph`、`pgrdf`、`fsm_core`、`jsonschema`、`pg_durable`、`pg_mockable`、`pg_uuid_v8`、`pg_stat_backtrace`、`pg_projection`。
- 更新 48 个已有扩展的软件包元数据，包括 `timescaledb 2.28.0`、`timescaledb_toolkit 1.23.0`、`pg_task 2.1.29`、`pg_search 0.24.0`、`pg_clickhouse 0.3.2`、`pg_graphql 1.6.1`、`documentdb 0.112`、`toastinfo 1.7`、`wrappers 0.6.1`、`pgclone 4.3.2` 等；没有扩展被移除或降级。
- 新增 PostgreSQL 19 beta 的安装、构建、配置支持。PG19 可以作为显式指定的安装版本使用，但自动探测、目录展示与 latest alias 的稳定默认版本仍保持为 PostgreSQL 18。
- 新增 `pg19` 软件包别名与 PG19 分类别名解析。PG19 分类别名借用 PostgreSQL 18 的可见性模板，并且 beta 软件包展开只包含 PGDG 来源条目。
- `pig sty conf -v 19` 会在模板支持时自动启用 `beta` 仓库模块；当模板没有针对 PG19 beta 调优，或无法自动启用 beta 仓库时，会给出明确警告。
- 修复 Patroni 集群操作：`patronictl restart`、`reinit`、`switchover`、`failover` 现在会传入解析出的 `CLUSTER_NAME`；`pig pt list` 也支持可选集群名参数。
- `pig build pgrx` 的默认 `pgrx` 版本从 `0.18.0` 升级到 `0.18.1`。
- 发布元数据更新到 `v1.4.2`，刷新 Go module checksum，并补充 PG19 alias / 配置生成与 Patroni cluster-scope 行为的针对性测试。

## 校验和

```bash
790afe4d6622cb041b06c622bc466cb1b2960a77487f368238027fb4a3a5ef93  pig-1.4.2-1.aarch64.rpm
ef918166b38a5eb1d108a928718c9e2cb8c3590e5a1f72effee942faca9b4bea  pig-1.4.2-1.x86_64.rpm
3e37ff22aed076cbdd453911dc89fcc9340b1a4faac62c0580094bc1eb2d6273  pig-v1.4.2.darwin-amd64.tar.gz
5eb7db776cb149331ebb33e3e6164e1cf711d0107941b92c6930a1d4c4b4eb23  pig-v1.4.2.darwin-arm64.tar.gz
c536c324e40a861217e31f4699ee5f0e6c2daeb4e6f0f0e8cc5f606da9d787eb  pig-v1.4.2.linux-amd64.tar.gz
8b2d5746264a95269535e5a426f78fe0020f73fa3391fcb613f274551c4786ab  pig-v1.4.2.linux-arm64.tar.gz
566e06f6da1fe9d635c41258d20cd9ff10de4e6e74b3b41ba2c6204ba22743c8  pig_1.4.2-1_amd64.deb
8c09e741975cb2f74b0f88c5995a8fa43d6c30a9a7ab7aaf0b8d83a7c66e1fc1  pig_1.4.2-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v1.4.2
