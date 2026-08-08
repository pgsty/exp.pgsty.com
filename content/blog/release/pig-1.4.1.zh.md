---
title: "pig v1.4.1"
linkTitle: "v1.4.1"
date: 2026-05-01
author: "冯若航"
description: "510 个扩展，支持 Ubuntu 26.04，仓库校准"
categories: [release]
tags: [Release, pig]
weight: 60
---

- 扩展目录更新到 **510** 个扩展，新增 3 个扩展，更新 17 个扩展。
- 新增 Ubuntu 26.04 `resolute` 支持，移除 Ubuntu 20.04 `focal` 支持。
- 将 `el9.aarch64` 特例中的 `patroni` / `patroni-etcd` 提升到 `4.1.2`。
- 校准上游软件仓库定义。

## 校验和

```bash
2b96e06d26e7425b13ac1f27d620b24b258f232bfc1d84c0b3aa2ee6505ea8aa  pig-1.4.1-1.aarch64.rpm
30a68d2fb97bb1d146ec57bcec2f279ce7fa4cf075fdcc9afc3d143f9a365896  pig-1.4.1-1.x86_64.rpm
ff4ac1a15f6a1e0aa935922a4e402a428fd3579c0143a5e411e835089a55cc2c  pig-v1.4.1.darwin-amd64.tar.gz
a23048d854bc2bef74a2b5cf42bd2f4aae79f3c9df3181a829ddf2167d939dc2  pig-v1.4.1.darwin-arm64.tar.gz
74feec28ee879853633d8e9f3722c95aa25c47a3d3f6fb5bde3f3609b5c09378  pig-v1.4.1.linux-amd64.tar.gz
d50d1ce2b0d682a4ced72a4a11e6bddbd90f9dccbd16eae886045845eec83104  pig-v1.4.1.linux-arm64.tar.gz
3fe640c3b6678fe4cef527a58dca54285f15d56c8fe0b3c2ed8b6879e1e91d41  pig_1.4.1-1_amd64.deb
d09fd6e747cb65acda225ffd5448a8fba3f676ce8044f4237d75a59b3d6a5b4e  pig_1.4.1-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v1.4.1
