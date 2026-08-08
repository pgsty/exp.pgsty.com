---
title: "pig v0.6.2"
linkTitle: "v0.6.2"
date: 2025-10-03
author: "冯若航"
description: "正式提供 PG 18 支持"
categories: [release]
tags: [Release, pig]
weight: 230
---

- 使用 PG 18 官方正式仓库取代原本的 Testing Beta 仓库 instead of testing repo
- 在接收 Pigsty 版本字符串的时候，自动添加 `v` 前缀
- 改进了网络检查与下载的逻辑

## 校验和

```bash
01f5b7dc20644226c762dbb229768347  pig_0.6.2-1_amd64.deb
ce4f00256adc12cbea91467b7f2241cd  pig_0.6.2-1_arm64.deb
cefc36ae8f348aede533b30836fba720  pig-0.6.2-1.aarch64.rpm
d04a287c6eb92b11ecbf99542c2db602  pig-0.6.2-1.x86_64.rpm
e637ca86a7f38866c67686b060223d9a  pig-v0.6.2.darwin-amd64.tar.gz
79749bc69c683586bd8d761bdf6af98e  pig-v0.6.2.darwin-arm64.tar.gz
ad4f02993c7d7d8eec142f0224551bb4  pig-v0.6.2.linux-amd64.tar.gz
9793affa4a0cb60e9753e65b7cba3dca  pig-v0.6.2.linux-arm64.tar.gz
```

发布：https://github.com/pgsty/pig/releases/tag/v0.6.2
