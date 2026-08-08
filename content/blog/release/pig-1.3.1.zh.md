---
title: "pig v1.3.1"
linkTitle: "v1.3.1"
date: 2026-03-05
author: "冯若航"
description: "PG13 退役，支持窗口统一为 PG14-18，扩展增至 464"
categories: [release]
tags: [Release, pig]
weight: 110
---

这是从 `v1.3.0` 到 `v1.3.1` 的一次小型维护版本。

- 由于 PGDG 上游已移除 PG13 归档与分发，pig 同步移除 PG13 安装/构建支持。
- 活跃支持的 PostgreSQL 主版本现在为 **14-18**。
- 扩展目录刷新（`461 -> 464`），新增 `pg_pinyin`、`pg_eviltransform`、`qos`。
- Percona PPG 上游仓库更新到 `18.3`。
- 修复 `pig build` 依赖/构建同步问题，rsync 增加 `--keep-dirlinks` 参数。
- YUM 仓库中 Nginx 从 `infra` 模块拆分为独立模块索引（`nginx`）。

## 校验和

```bash
196e57c7dd46cdedd90ab75965a766f74aabc3bc23ddc8fb757473647bed7b8f  pig-1.3.1-1.aarch64.rpm
e4bdd52ef635524d5aec95f6a5abd76bd49940584ecbb00bd309a4f9186292ac  pig-1.3.1-1.x86_64.rpm
4f3f9479344c158e1c5edc3003471be6b595c01b7d86104bf676b34f8faadce5  pig-v1.3.1.darwin-amd64.tar.gz
05ae2f550ef5062ab5714518a24bbf52f48079ca6d0190359fae5b8f4cb7f20d  pig-v1.3.1.darwin-arm64.tar.gz
940645497e907e56bfd387a478e580ac930aaa72593cc9d04225a08b37880ec4  pig-v1.3.1.linux-amd64.tar.gz
8b2c204fd6c933a1097cd1cd0ce491b02ba5c0025626a331a199684ceca3ab43  pig-v1.3.1.linux-arm64.tar.gz
1cfc23d147795cc4c1ea9596e6978d79ff1ec34c02850fbb224f7c2844548ea5  pig_1.3.1-1_amd64.deb
e495678ae1c762194a56e8c9969fd2109e7a59830f34a4747039fb978f7820cc  pig_1.3.1-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v1.3.1
