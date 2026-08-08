---
title: "pig v1.4.0"
linkTitle: "v1.4.0"
date: 2026-04-19
author: "冯若航"
description: "510 个扩展，pgrx 0.18.0，更多构建规格"
categories: [release]
tags: [Release, pig]
weight: 70
---

- 刷新扩展目录，可用扩展总数增加到 **510**，并更新 `timescaledb 2.26.3`、`decoderbufs 3.5.0`、`pgclone 4.0.0`、`nominatim_fdw 1.3` 等版本。
- 默认 `pgrx` 从 `0.17.0` 升级到 `0.18.0`，同步对齐相关 Rust 扩展构建版本。
- 为 `pig build get` 刷新权威源码包映射，覆盖 Cloudberry / OrioleDB 构建输入，以及 RDKit / OneSparse 相关附加源码。
- 修复 `repo set` 标志位隔离问题，并修正 PostgreSQL schema 级维护 SQL。
- `el9.aarch64` 上的 `patroni` 升级到 `4.1.1`。

## 校验和

```bash
c8d2f46ea1b25f7d4665ee0994f0cb403a59f1464f80b3ecfa575ac283e5ecd0  pig-1.4.0-1.aarch64.rpm
fb1fd2f4f1e71894779de7b11a42960c09261620dffa0b54ff7f84e60efbf976  pig-1.4.0-1.x86_64.rpm
aa08045a31c26b9a6bfb770753817581c819022a6ed899e44f7b5a31f57f1733  pig-v1.4.0.darwin-amd64.tar.gz
80e50dd2ccd08d4a4016e85518186e156498e00c56a898e65acb96466db339f0  pig-v1.4.0.darwin-arm64.tar.gz
e425bf35ab6cb7907e94caca802b4418e3baf4bb1642dd957ab4baaa9db9f583  pig-v1.4.0.linux-amd64.tar.gz
840a21695955d64af7df12f7157b49573b18586bb2bf9cc5e7079074b86d39b7  pig-v1.4.0.linux-arm64.tar.gz
401d91bae78b14e3dcc338aaac9e451e94282c79efbe9affabcfeb8b36ece587  pig_1.4.0-1_amd64.deb
d60515f72fb9f8963554dc5668d2398e5ecefd0153a7756a9d555de90115bcce  pig_1.4.0-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v1.4.0
