---
title: "pig v0.7.1"
linkTitle: "v0.7.1"
date: 2025-11-10
author: "冯若航"
description: "新网站，改进容器内的使用体验"
categories: [release]
tags: [Release, pig]
weight: 210
---

- 全新的网站： /ext/
- 修复了不必要的 sudo 使用问题，现在可以方便的在容器中使用
- 允许 pig ext link 命令使用形如 pg17 pg18 的参数形式
- 新增环境变量 `PIG_NO_SUDO`，强制不使用 sudo 执行命令
- [RPM 变更日志](https://pigsty.cc/docs/repo/pgsql/rpm#2025-11-10)：为几乎所有扩展新增 PG 18 支持
- [DEB 变更日志](https://pigsty.cc/docs/repo/pgsql/deb#2025-11-10)：为几乎所有扩展新增 PG 18 支持
- [Infra 变更日志](https://pigsty.cc/docs/repo/infra/log/)：例行更新至最新版本

## 校验和

```bash
a696c9ec784e2fc248e5f3d87cc8aae4116e890f78c5997957d30593f2c85ca6  pig-0.7.1-1.aarch64.rpm
f669538a99cd1dc592d3005b949628fcceb9e78114fc78862d7726b340ee194d  pig-0.7.1-1.x86_64.rpm
e42bdaaf93b720c5b76b32b57362320e4b447109740c76089aefe030b7c8b836  pig-v0.7.1.darwin-amd64.tar.gz
b4c240aadad34e785666ee0a755d9b7455724f790c2d088a1dd7c37ad3b2a457  pig-v0.7.1.darwin-arm64.tar.gz
ffc687add0ca71ac90cba5749c8a7a6075cf7618cba85584072831cf3eb182f7  pig-v0.7.1.linux-amd64.tar.gz
7b0d1f158150d0a40c525692f02b6bce9f5b4ac523a4e59278d702c334e222e1  pig-v0.7.1.linux-arm64.tar.gz
43e91a3bea273d7cacb2d7a58c0a5745501dbd06348b5cb3af971171fae70268  pig_0.7.1-1_amd64.deb
fc2a34aeb46e07cb0ae93611de47d6622c3bd46fe4c415ce4c9091840e0e08a2  pig_0.7.1-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v0.7.1
