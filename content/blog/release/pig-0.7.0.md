---
title: "pig v0.7.0"
linkTitle: "v0.7.0"
date: 2025-11-05
author: "Ruohang Feng"
description: "Build Enhancement and massive upgrade"
categories: [release]
tags: [Release, pig]
weight: 220
---

- Add support for Debian 13 and EL 10 distributions
- Massive extension updates to the latest versions with PostgreSQL 18 support
- Almost all Rust extensions now support PG 18 via pgrx 0.16.1
- `pig build` command overhaul
  - `pig build pkg <pkg>` will now download source, prepare deps, and build in one go
  - `pig build pgrx` is now separated from `pig build rust`
  - `pig build pgrx [-v pgrx_version]` can now use existing PG installation directly
  - `pig build dep` will now handle extension dependencies on both EL and Debian systems
  - `pig build ext` now has more compact and elegant output, can build RPM on EL without build script
  - `pig build spec` now supports downloading spec files directly from Pigsty repo
  - `pig build repo` / `pig repo add` / `pig repo set` now use `node,pgsql,infra` as default repo modules instead of `node,pgdg,pigsty`
- Optimized error logging
- Brand new catalog website based on hugo and hextra

## Checksums

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

Release: https://github.com/pgsty/pig/releases/tag/v0.7.0
