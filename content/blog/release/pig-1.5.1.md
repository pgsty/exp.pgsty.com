---
title: "pig v1.5.1"
linkTitle: "v1.5.1"
date: 2026-07-08
author: "Ruohang Feng"
description: "PG kernel fork updates, mirror mode, bug fixes"
categories: [release]
tags: [Release, pig]
weight: 30
---

Pig `v1.5.1` updates PG kernel forks to the latest package names.

## Highlights

- Add mirror/proxy mode to repo, build, sty, update, and extension update workflows; `pig build rust -m` also configures Cargo mirror settings with `rsproxy.cn`.
- Add explicit PostgreSQL 19 beta build switches: `pig build repo --beta`, `pig build tool --beta`, and `pig build pgrx -b`, while keeping PostgreSQL 18 and PG14-18 as the stable defaults.
- Refresh kernel and fork package aliases for IvorySQL, PolarDB, OrioleDB, OpenHaloDB, Babelfish, and the pgEdge suite.
- Improve the Cloudberry package build flow for `cloudberry`, `cloudberry-backup`, and `cloudberry-pxf`.
- Refresh source/package metadata for Cloudberry, Babelfish, OrioleDB, pgEdge, PolarDB, `polarstore`, `zlog`, `libpgfeutils`, and `libfq`.
- Improve repository generation for newer EL release strings, including PGDG on EL9.6+ / EL10+ and EPEL's EL10 `10z` stream.
- Refresh extension versions including `pg_ivm 1.15`, `spock 5.0.10`, `snowflake 2.5.0`, `pg_tde 2.2`, `decoderbufs 3.6.0`, and IvorySQL `5.4` packages.

## Checksums

```bash
bc83887d640ed299a967b4eda2ae6db621a985abfa022fccabf508f7ec7b98e3  pig-1.5.1-1.aarch64.rpm
f0eab8e638d9e00a9172751446db869d0fe6ca7f382c7d540a931e0764014c0a  pig-1.5.1-1.x86_64.rpm
b32d894dc444ef2b9ec00816d50d82b5834e64c35b3bb18f08b6286a7ca8e8e7  pig-v1.5.1.darwin-amd64.tar.gz
4d768829b7e93fac6c732e27f665d3ab3945ec8bc1c336e5b91980932e8c9932  pig-v1.5.1.darwin-arm64.tar.gz
69f4a016af52f1ee8f1a1ffc1e405bb3be551c3813b6d24f70ef8394330be5eb  pig-v1.5.1.linux-amd64.tar.gz
f49becb5fd556b36a9aa8de0c27bdbe210f7958f59254d780774828f2340e77b  pig-v1.5.1.linux-arm64.tar.gz
a0d15145409d8a2629a74d3071f7af593e470920f22d9af4bf6f96725dbb6d49  pig_1.5.1-1_amd64.deb
f05b9b5abef5992ed16cbb5b6a6e3e5e58230072e3665ecc57b9ce2df3edb9a6  pig_1.5.1-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.5.1
