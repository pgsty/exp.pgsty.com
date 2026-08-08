---
title: "pig v1.4.0"
linkTitle: "v1.4.0"
date: 2026-04-19
author: "Ruohang Feng"
description: "510 extensions, pgrx 0.18.0, more building specs"
categories: [release]
tags: [Release, pig]
weight: 70
---

- Refresh the extension catalog and increase the total available extensions to **510**, with version bumps such as `timescaledb 2.26.3`, `decoderbufs 3.5.0`, `pgclone 4.0.0`, and `nominatim_fdw 1.3`.
- Bump the default `pgrx` version from `0.17.0` to `0.18.0` and align related Rust extension builds.
- Refresh authoritative source bundles for `pig build get`, covering Cloudberry / OrioleDB build inputs and bundled artifacts for RDKit and OneSparse-related packages.
- Fix `repo set` flag isolation and correct schema maintenance SQL.
- Bump `patroni` to `4.1.1` for `el9.aarch64`.

## Checksums

```bash
c8d2f46ea1b25f7d4665ee0994f0cb403a59f1464f80b3ecfa575ac283e5ecd0  pig-1.4.0-1.aarch64.rpm
fb1fd2f4f1e71894779de7b11a42960c09261620dffa0b54ff7f84e60efbf976  pig-1.4.0-1.x86_64.rpm
aa08045a31c26b9a6bfb770753817581c819022a6ed899e44f7b5a31f57f1733  pig-v1.4.0.darwin-amd64.tar.gz
80e50dd2ccd08d4a4016e85518186e156498e00c56a898e65acb96466db339f0  pig-v1.4.0.darwin-arm64.tar.gz
e425bf35ab6cb7907e94caca802b4418e3baf4bb1642dd957ab4baaa9db9f583  pig-v1.4.0.linux-amd64.tar.gz
840a21695955d64af7df12f7157b49573b18586bb2bf9cc5e7079074b86d39b7  pig-v1.4.0.linux-arm64.tar.gz
401d91bae78b14e3dcc338aaac9e451e94282c79efbe9affabcfeb8b36ece587  pig_1.4.0-1_amd64.deb
d60515f72fb9f8963554dc5668d2398e5ecefd0153a7756a9d555de90115bcce  pig_1.4.0-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.4.0
