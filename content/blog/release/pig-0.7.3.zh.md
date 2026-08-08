---
title: "pig v0.7.3"
linkTitle: "v0.7.3"
date: 2025-11-24
author: "冯若航"
description: "修复 el10 & debian13 仓库配置"
categories: [release]
tags: [Release, pig]
weight: 190
---

- 新增 pig repo reload 命令，更新仓库元数据
- 修复 EL PGDG sysupdate aarch64 仓库问题。
- 修复 EL10.aarch64 PGDG 仓库重命名问题。
- 订正了若干扩展版本
- 更新 Pigsty 版本至 3.7.0

## 校验和

```bash
786d72f6b685d6d6abf5f255f0a7de9204988a05630a26a53bfc7631823c0c6f  pig-0.7.3-1.aarch64.rpm
da59e24ef79d1164e348bacc43e3222e8e2778ec0e103e7ffc0c6df064758e8f  pig-0.7.3-1.x86_64.rpm
73062a979749095e89abc07dd583d34d4f57908bb4ee935cf7640f129ca6a2cb  pig-v0.7.3.darwin-amd64.tar.gz
ca5f5576f6d0d9be1d10cad769821be9daa62220b2fb56b94d6e4c0cede6da61  pig-v0.7.3.darwin-arm64.tar.gz
d193b4b87cf9a6e4775b1b07709802d30f0233ccb1b728843a09decb545168d3  pig-v0.7.3.linux-amd64.tar.gz
e7f612df0e8e4d9fac6df3765862b9e491bb50aad651856abf7a6935986e6f99  pig-v0.7.3.linux-arm64.tar.gz
3d5306ce95dcf704dd498b05325d942637564b13115f1e5a5bb9ef6781df1ba6  pig_0.7.3-1_amd64.deb
32e695ba2d49a741d8cd92008f8f2dec29f10754d35b732035f48517b382c30d  pig_0.7.3-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v0.7.3
