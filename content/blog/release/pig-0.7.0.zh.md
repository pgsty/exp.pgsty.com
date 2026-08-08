---
title: "pig v0.7.0"
linkTitle: "v0.7.0"
date: 2025-11-05
author: "冯若航"
description: "强化 build 能力，大批量包更新"
categories: [release]
tags: [Release, pig]
weight: 220
---

- 提供针对 Debian 13 和 EL 10 发行版的支持
- 大批量扩展更新至最新版本，带有 PostgreSQL 18 支持。
- 几乎所有 Rust 扩展现已通过 pgrx 0.16.1 支持 PG 18
- `pig build` 命令彻底重做
  - `pig build pkg <pkg>` 现在会一条龙完成扩展的下载，依赖安装，构建
  - `pig build pgrx` 命令现在从 `pig build rust` 中分离
  - `pig build pgrx [-v pgrx_version]` 现在可以直接使用现有的 PG 安装
  - `pig build dep` 现在会处理 EL 和 Debian 系统下的扩展依赖
  - `pig build ext` 命令现在有了更为紧凑和美观的输出，可在 EL 下不依赖 build 脚本直接构建 RPM
  - `pig build spec` 现在支持直接从 Pigsty 仓库下载 spec 文件包
  - `pig build repo` / `pig repo add` / `pig repo set` 现在默认使用 `node,pgsql,infra` 仓库模块，取代原本的 `node,pgdg,pigsty`
- 大量优化了错误日志记录。
- 基于 hugo 与 hextra 全新目录网站

## 校验和

```bash
ad60f9abcde954769e46eb23de61965e  pig_0.7.0-1_amd64.deb
aa15d7088d561528e38b2778fe8f7cf9  pig_0.7.0-1_arm64.deb
05549fe01008e04f8d5a59d4f2a5f0b8  pig-0.7.0-1.aarch64.rpm
0cc9e46c7c72d43c127a6ad115873b67  pig-0.7.0-1.x86_64.rpm
ddacfb052f3f3e5567a02e92fdb31cdd  pig-v0.7.0.darwin-amd64.tar.gz
17d25b565308d3d35513e4b0d824946b  pig-v0.7.0.darwin-arm64.tar.gz
ee7e055ceff638039956765fb747f80b  pig-v0.7.0.linux-amd64.tar.gz
284e674807b87447d4b33691fd7a420d  pig-v0.7.0.linux-arm64.tar.gz
```

发布：https://github.com/pgsty/pig/releases/tag/v0.7.0
