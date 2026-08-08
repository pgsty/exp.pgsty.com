---
title: "pig v1.5.1"
linkTitle: "v1.5.1"
date: 2026-07-08
author: "冯若航"
description: "PG 内核分支包更新，镜像模式，修复若干问题"
categories: [release]
tags: [Release, pig]
weight: 30
---

Pig `v1.5.1` 是一次构建与仓库维护版本，更新了多款 PG 内核分支包。

## 主要变化

- 镜像/代理模式覆盖 repo、build、sty、update、ext update 等流程；`pig build rust -m` 会写入 Cargo 镜像配置并使用 `rsproxy.cn`。
- 新增 PostgreSQL 19 beta 的 repo、tool、pgrx 显式构建开关：`pig build repo --beta`、`pig build tool --beta`、`pig build pgrx -b`；稳定默认值仍保持 PostgreSQL 18 与 PG14-18 窗口。
- 刷新 IvorySQL、PolarDB、OrioleDB、OpenHaloDB、Babelfish、pgEdge 套件等内核与 fork 包别名。
- 改进 Cloudberry 套件构建流程，覆盖 `cloudberry`、`cloudberry-backup`、`cloudberry-pxf`。
- 刷新 Cloudberry、Babelfish、OrioleDB、pgEdge、PolarDB、`polarstore`、`zlog`、`libpgfeutils`、`libfq` 等源码与包元数据。
- 改进较新 EL release 字符串处理，包括 EL9.6+ / EL10+ 上的 PGDG 仓库，以及 EPEL 在 EL10 上使用的 `10z` stream。
- 刷新扩展版本，包括 `pg_ivm 1.15`、`spock 5.0.10`、`snowflake 2.5.0`、`pg_tde 2.2`、`decoderbufs 3.6.0`、IvorySQL `5.4` 包。

## 校验和

```bash
bc83887d640ed299a967b4eda2ae6db621a985abfa022fccabf508f7ec7b98e3  pig-1.5.1-1.aarch64.rpm
f0eab8e638d9e00a9172751446db869d0fe6ca7f382c7d540a931e0764014c0a  pig-1.5.1-1.x86_64.rpm
b32d894dc444ef2b9ec00816d50d82b5834e64c35b3bb18f08b6286a7ca8e8e7  pig-v1.5.1.darwin-amd64.tar.gz
4d768829b7e93fac6c732e27f665d3ab3945ec8bc1c336e5b91980932e8c9932  pig-v1.5.1.darwin-arm64.tar.gz
69f4a016af52f1ee8f1a1ffc1e405bb3be551c3813b6d24f70ef8394330be5eb  pig-v1.5.1.linux-amd64.tar.gz
f49becb5fd556b36a9aa8de0c27bdbe210f7958f59254d780774828f2340e77b  pig-v1.5.1.linux-arm64.tar.gz
a0d15145409d8a2629a74d3071f7af593e470920f22d9af4bf6f96725dbb6d49  pig_1.5.1-1_amd64.deb
f05b9b5abef5992ed16cbb5b6a6e3e5e58230072e3665ecc57b9ce2df3edb9a6  pig_1.5.1-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v1.5.1
