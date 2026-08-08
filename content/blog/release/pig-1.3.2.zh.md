---
title: "pig v1.3.2"
linkTitle: "v1.3.2"
date: 2026-03-23
author: "冯若航"
description: "例行元数据更新，新增 `pg tune` 与构建别名"
categories: [release]
tags: [Release, pig]
weight: 100
---

例行维护版本。

- 例行刷新部分扩展版本元数据与扩展目录条目，扩展版本更新。
- 新增 `pig pg tune` 子命令，可根据硬件资源与工作负载画像生成 PostgreSQL 调优参数建议。
- 为 `pig build get` 新增 `pdu` 与 `pgdog` 两个源码包 alias。
- 调整 pgext.cloud 的 URL 至新版本的扩展目录 pigsty.io/ext

## 校验和

```bash
d760f47652ff3e2e4a61eb7b9a68ca68665b2b36c187c52f5eaf50d2f007d8f3  pig-1.3.2-1.aarch64.rpm
c2e02e62497f4c2055a9b448ddb3a24c618fcd488580c28b2b9a0e7cedacef55  pig-1.3.2-1.x86_64.rpm
b8d066ddefa4530946c74c30e7e4acdab6abf8da70a47dcfe2a77719b79e397f  pig-v1.3.2.darwin-amd64.tar.gz
a90e78d879fd720fd2865870c696aed7952558d5ae75591deced3121f2aab1f9  pig-v1.3.2.darwin-arm64.tar.gz
2fe3a9ffbb6383154dfd25ed79420b210828eabf6a96a8af6e8feb9d744b9559  pig-v1.3.2.linux-amd64.tar.gz
522290aaf14f98f0bae83ce75cc76749f2a4e72742eb5c3cba36a1d2fa4d12c2  pig-v1.3.2.linux-arm64.tar.gz
d6c1cf2c52962045f6bbfb2a669058e7f903088526591d6c939e7723f3928d30  pig_1.3.2-1_amd64.deb
4352385c629b26a1837054445a546da89591499848b557699c2fb70fde9377aa  pig_1.3.2-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v1.3.2
