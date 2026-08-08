---
title: "pig v0.6.0"
linkTitle: "v0.6.0"
date: 2025-07-17
author: "冯若航"
description: "423 个扩展，percona pg_tde，mcp 工具箱"
categories: [release]
tags: [Release, pig]
weight: 250
---

- 新扩展目录：[https://ext.pgsty.com](https://ext.pgsty.com)
- 新子命令：`pig install` 简化 `pig ext install`
- 添加新内核支持：带 pg_tde 的 percona
- 添加新包：Google GenAI MCP 数据库工具箱
- 添加新仓库：percona 仓库和 clickhouse 仓库
- 将扩展摘要信息链接更改为 https://ext.pgsty.com
- 修复 orioledb 在 Debian/Ubuntu 系统上的问题
- 修复 EL 发行版上的 epel 仓库
- 将 golang 升级到 1.24.5
- 将 pigsty 升级到 v3.6.0

## 校验和

```bash
1804766d235b9267701a08f95903bc3b  pig_0.6.0-1_amd64.deb
35f4efa35c1eaecdd12aa680d29eadcb  pig_0.6.0-1_arm64.deb
b523b54d9f2d7dcc5999bcc6bd046b1d  pig-0.6.0-1.aarch64.rpm
9434d9dca7fd9725ea574c5fae1a7f52  pig-0.6.0-1.x86_64.rpm
f635c12d9ad46a779aa7174552977d11  pig-v0.6.0.linux-amd64.tar.gz
165af4e63ec0031d303fe8b6c35c5732  pig-v0.6.0.linux-arm64.tar.gz
```

发布：https://github.com/pgsty/pig/releases/tag/v0.6.0
