---
title: "pig v1.3.1"
linkTitle: "v1.3.1"
date: 2026-03-05
author: "Ruohang Feng"
description: "Retire PG13 defaults, unify PG14-18 support window, 464 extensions"
categories: [release]
tags: [Release, pig]
weight: 110
---

This is a small maintenance release from `v1.3.0` to `v1.3.1`.

- PG13 install/build support is removed because PGDG upstream has dropped PG13 archive/distribution.
- Active supported PostgreSQL major versions are now **14-18**.
- Refresh extension catalog (`461 -> 464`), including `pg_pinyin`, `pg_eviltransform`, and `qos`.
- Percona PPG upstream repo is bumped to `18.3`.
- Fix `pig build` dependency/build sync issues; rsync now uses `--keep-dirlinks`.
- In YUM repos, Nginx is split out from `infra` into its own module index (`nginx`).

## Checksums

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

Release: https://github.com/pgsty/pig/releases/tag/v1.3.1
