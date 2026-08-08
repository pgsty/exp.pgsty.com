---
title: "pig v0.8.0"
linkTitle: "v0.8.0"
date: 2025-12-26
author: "Ruohang Feng"
description: "440 extensions, remove sysupdate repo"
categories: [release]
tags: [Release, pig]
weight: 160
---

## Extension Updates
- Total extensions reached 440
- New extension: [pg_ai_query](https://github.com/benodiwal/pg_ai_query) 0.1.1
- New extension: [pg_textsearch](https://github.com/timescale/pg_textsearch) 0.1.0
- New extension: [pg_clickhouse](https://github.com/clickhouse/pg_clickhouse/) 0.1.0
- pg_biscuit upgraded from 1.0 to 2.0.1 (switched to new repo, renamed to biscuit)
- pg_search upgraded from 0.20.3 to 0.20.5
- pg_duckdb upgraded to official release 1.1.1
- vchord_bm25 upgraded from 0.2.2 to 0.3.0
- pg_semver upgraded from 0.40.0 to 0.41.0
- pg_timeseries upgraded from 0.1.7 to 0.1.8
- Fixed debian/ubuntu pg18 extension issues: supautils, pg_summarize, pg_vectorize, pg_tiktoken, pg_tzf, pglite_fusion, pgsmcrypto, pgx_ulid, plprql
- Pigsty version synced to 4.0.0

## Repository Updates
- Removed pgdg yum sysupdate repo due to upstream changes
- Removed pgdg yum llvmjit package due to upstream changes
- Fixed patroni 3.0.4 duplicate package issue on el9.aarch64
- Added priority for el repo definitions, docker repo skipped when unavailable
- Added epel 10 / pgdg 9/10 OS minor version hotfix

## Checksums

```bash
e457832fb290e2f9975bf719966dc36e650bdcbf8505d319c9e0431f4c03bc9e  pig-0.8.0-1.aarch64.rpm
c97b1bfdd7541f0f464cab0ecc273e65535c8dd2603c38d5cf8dccbf7e95b523  pig-0.8.0-1.x86_64.rpm
d892f06d3d3b440671529f40e6cc7949686e0167e2a4758adc666b8a3d75254d  pig-v0.8.0.darwin-amd64.tar.gz
222413bafdf5a62dc682dac32ea1118cbc34ec3544e2a1b85076ec450b9cc7ae  pig-v0.8.0.darwin-arm64.tar.gz
d50aa9806bbab8fee5ad9228e104fc9e7ead48729228116b5bf889000791fedc  pig-v0.8.0.linux-amd64.tar.gz
d2f410f7b243a8323c8d479f462a0267ac72d217aa4a506c80b5a9927d12dff8  pig-v0.8.0.linux-arm64.tar.gz
4ccd330a995911d4f732e8c9d62aa0db479c21c9596f64c4bc129ec43f156abe  pig_0.8.0-1_amd64.deb
5cb9eccce659110f3ba58e502575564bd6befffd51992a43d84df5a17f8eb8a0  pig_0.8.0-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v0.8.0
