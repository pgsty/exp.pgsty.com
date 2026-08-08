---
title: "pig v0.7.1"
linkTitle: "v0.7.1"
date: 2025-11-10
author: "Ruohang Feng"
description: "New Website, improve in-docker experience"
categories: [release]
tags: [Release, pig]
weight: 210
---

- The brand-new website: /ext/
- Remove unnecessary sudo usage, now can be used inside docker
- Allow using `pg18`, `pg17` arg format in pig ext link command
- Add environment var `PIG_NO_SUDO` to force not using sudo
- [RPM Changelog](https://pigsty.io/docs/repo/pgsql/rpm#2025-11-10): Add PG 18 support to almost all extensions
- [DEB Changelog](https://pigsty.io/docs/repo/pgsql/deb#2025-11-10): Add PG 18 support to almost all extensions
- [Infra Changelog](https://pigsty.io/docs/repo/infra/#2025-11-08): Routine update to the latest version

## Checksums

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

Release: https://github.com/pgsty/pig/releases/tag/v0.7.1
