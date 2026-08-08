---
title: "pig v0.8.0"
linkTitle: "v0.8.0"
date: 2025-12-26
author: "冯若航"
description: "440 extensions，移除 sysupdate 仓库"
categories: [release]
tags: [Release, pig]
weight: 160
---

## 扩展更新
- 扩展总数达到 440 个
- 新增扩展：[pg_ai_query](https://github.com/benodiwal/pg_ai_query) 0.1.1
- 新增扩展：[pg_textsearch](https://github.com/timescale/pg_textsearch) 0.1.0
- 新增扩展：[pg_clickhouse](https://github.com/clickhouse/pg_clickhouse/) 0.1.0
- pg_biscuit 从 1.0 升级至 2.0.1（切换至新仓库，更名为 biscuit）
- pg_search 从 0.20.3 升级至 0.20.5
- pg_duckdb 升级至官方正式版 1.1.1
- vchord_bm25 从 0.2.2 升级至 0.3.0
- pg_semver 从 0.40.0 升级至 0.41.0
- pg_timeseries 从 0.1.7 升级至 0.1.8
- 修复 debian/ubuntu pg18 扩展问题：supautils、pg_summarize、pg_vectorize、pg_tiktoken、pg_tzf、pglite_fusion、pgsmcrypto、pgx_ulid、plprql
- pigsty 版本号同步至 4.0.0

## 仓库更新
- 因上游变更移除 pgdg yum sysupdate 仓库
- 因上游变更移除 pgdg yum llvmjit 软件包
- 修复 el9.aarch64 上 patroni 3.0.4 重复软件包问题
- 为 el 仓库定义添加优先级，docker 仓库不可用时自动跳过
- 添加 epel 10 / pgdg 9/10 操作系统小版本热修复

## 校验和

```bash
e457832fb290e2f9975bf719966dc36e650bdcbf8505d319c9e0431f4c03bc9e  pig-0.8.0-1.aarch64.rpm
c97b1bfdd7541f0f464cab0ecc273e65535c8dd2603c38d5cf8dccbf7e95b523  pig-0.8.0-1.x86_64.rpm
d892f06d3d3b440671529f40e6cc7949686e0167e2a4758adc666b8a3d75254d  pig-v0.8.0.darwin-amd64.tar.gz
222413bafdf5a62dc682dac32ea1118cbc34ec3544e2a1b85076ec450b9cc7ae  pig-v0.8.0.darwin-arm64.tar.gz
d50aa9806bbab8fee5ad9228e104fc9e7ead48729228116b5bf889000791fedc  pig-v0.8.0.linux-amd64.tar.gz
d2f410f7b243a8323c8d479f462a0267ac72d217aa4a506c80b5a9927d12dff8  pig-v0.8.0.linux-arm64.tar.gz
4ccd330a995911d4f732e8c9d62aa0db479c21c9596f64c4bc129ec43f156abe  pig_0.8.0-1_amd64.deb
5cb9eccce659110f3ba58e502575564bd6befffd51992a43d84df5a17f8eb8a0  pig_0.8.0-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v0.8.0
