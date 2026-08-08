---
title: "pig v1.6.1"
linkTitle: "v1.6.1"
date: 2026-07-30
author: "冯若航"
description: "pig v1.6.1 刷新了内置的扩展目录，并将内嵌的 Pigsty 版本对齐到 4.5.0。"
categories: [release]
tags: [Release, pig]
weight: 10
---

`pig` v1.6.1 是 [v1.6.0](/zh/release/pig-1.6.0/) 之上的维护版本：没有新增命令，也没有参数变更，
这次发布的重点是二进制里自带的那份扩展目录。

## 变更内容

- **扩展目录刷新**：内置的 `extension.csv` 依据 Pigsty 软件仓库重新生成，`pig ext list`
  与 `pig install` 无需先跑一次 `pig ext reload`，即可对齐当前的软件包版本。
- **Pigsty 版本对齐到 4.5.0**：`pig sty` 与 `pig status` 报告的内嵌 Pigsty 版本随之更新。
- **版本号同步**：构建元数据与 `pig update` 的版本字符串一并更新。

目录依然覆盖 PostgreSQL 14–18 上的 {{< param pgext_count >}} 个已打包扩展，
适用于 EL 8/9/10、Debian 12/13、Ubuntu 22/24/26，`x86_64` 与 `aarch64` 双架构。

## 升级方式

```bash
pig update                 # 通过系统包管理器就地升级
pig update -v 1.6.1        # 或者指定精确版本
```

全新安装会直接拿到 v1.6.1：

```bash
curl -fsSL https://repo.pigsty.cc/pig | bash   # 中国大陆镜像
curl -fsSL https://repo.pigsty.io/pig | bash   # 全球站点（Cloudflare CDN）
```

如果只想刷新目录、不升级二进制，也可以：

```bash
pig ext reload             # 把最新目录下载到 ~/.pig/extension.csv
```

完整版本历史见 [发布注记](/zh/release/)，安装包与校验和见
[GitHub 发布页](https://github.com/pgsty/pig/releases/tag/v1.6.1)。
