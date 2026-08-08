---
title: "pig v0.7.2"
linkTitle: "v0.7.2"
date: 2025-11-20
author: "冯若航"
description: "437 个扩展，修复 pig build 的一些问题"
categories: [release]
tags: [Release, pig]
weight: 200
---

- 批量更新扩展，数量达到 437 个
- 新增 PGDG EL10 Sysupdate 仓库
- 新增 LLVM APT 仓库
- 在 pig build 命令中使用可选的本地 extension.csv 扩展定义问题。

- 更新的扩展： vchord pg_later pgvectorscale pglite_fusion pgx_ulid pg_search citus timescaledb pg_profile pg_stat_monitor documentdb
- 新增的扩展：pglinter pg_typeid pg_enigma pg_retry pg_biscuit pg_weighted_statistics

## 校验和

```bash
f303c391fc28bc74832712e0aa58319abe0ebcae4f6c07fdf9a9e542b735d2ec  pig-0.7.2-1.aarch64.rpm
c096a61a4e3a49b1238659664bbe2cd7f29954c43fb6bb8e8e9fb271f95a612e  pig-0.7.2-1.x86_64.rpm
5e037c891dff23b46856485108d6f64bede5216dfbd4f38a481f0d0672ee910b  pig-v0.7.2.darwin-amd64.tar.gz
736b4b47999c543c3c886781f4d8dddbf4276f363c35c7bf50094b6f18d14600  pig-v0.7.2.darwin-arm64.tar.gz
20b13f059efed29dd76f6927b3e8d7b597c0c8d734f9e22ba3d0a2af6dbcd3bf  pig-v0.7.2.linux-amd64.tar.gz
9548b530c05f2ffdc8d73b8f890718d47b74a51eb62852a99c08b1b52e47f014  pig-v0.7.2.linux-arm64.tar.gz
b6faad9f92b926546a10f590274f2cb2afff21b9cea878094cfc5caf09e67d2c  pig_0.7.2-1_amd64.deb
452f73f1fa035e5417ab49fc51d797925550179ffcc023e8f03d80144309212a  pig_0.7.2-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v0.7.2
