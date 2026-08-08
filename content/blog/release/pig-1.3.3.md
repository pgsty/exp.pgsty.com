---
title: "pig v1.3.3"
linkTitle: "v1.3.3"
date: 2026-04-10
author: "Ruohang Feng"
description: "481 extensions and Go 1.26.2 update"
categories: [release]
tags: [Release, pig]
weight: 90
---

- Refresh extension catalog and increase total available extensions to **481**.
- Bump Go toolchain from `1.26.0` to `1.26.2`.

## Extension Updates

| Extension        | Old    | New    | Notes                    |
|:-----------------|:-------|:-------|:-------------------------|
| `timescaledb`    | 2.25.2 | 2.26.2 | available, PG15-18       |
| `pg_background`  | 1.8    | 1.9.2  | DEB only, PG14-18        |
| `pg_ivm`         | 1.13   | 1.14   | upgraded, PG14-18        |
| `system_stats`   | 3.2    | 4.0    | upgraded, PG14-18        |
| `nominatim_fdw`  | 1.1.0  | 1.2    | upgraded, PG14-18        |
| `pg_textsearch`  | 0.5.0  | 1.0.0  | PG17-18                  |
| `pg_clickhouse`  | 0.1.5  | 0.1.10 | available, PG14-18       |
| `pg_search`      | 0.22.2 | 0.22.6 | manual download, PG15-18 |
| `pg_store_plans` | 1.9    | 1.10   | upgraded, PG14-18        |
| `pg_dispatch`    |        | 0.1.5  | new, PG14-18             |
| `pg_fsql`        |        | 1.1.0  | new, PG14-18             |
| `pg_liquid`      |        | 0.1.7  | new, PG14-18             |
| `pg_regresql`    |        | 2.0.0  | new, PG14-18             |
| `pg_slug_gen`    |        | 1.0.0  | new, PG15-18             |
| `pg_stat_ch`     |        | 0.3.3  | new, PG16-18             |
| `pg_variables`   |        | 1.2.5  | new, PG14-18             |
| `pgcalendar`     |        | 1.1.0  | new, PG14-18             |
| `pgclone`        |        | 2.2.0  | new, PG14-18             |
| `pgelog`         |        | 1.0.2  | new, PG14-18             |
| `pglock`         |        | 1.0.0  | new, PG14-18             |
| `pgproto`        |        | 0.2.1  | new, PG14-18             |
| `postgresbson`   |        | 2.0.2  | new, PG14-18             |
| `rdf_fdw`        |        | 2.4.0  | new, PG14-18             |
| `parray_gin`     |        | 1.4.0  | new, PG14-18             |

## Checksums

```bash
e74418061ea975fbc3e8a89b31f274d7dc3617d12b9d681e5c8ef03584392088  pig-1.3.3-1.aarch64.rpm
8450e3e1076425fc8a10f24cc5fd833c3d2d880bab12baff5c10e59a31f62231  pig-1.3.3-1.x86_64.rpm
952a0e94b9020fca5add91f8e9a398fbedfda5d2e5c8736e59ddaa2b7152c826  pig-v1.3.3.darwin-amd64.tar.gz
c896b4fd44b19a250f4c3c47dc78643e10e92fde8cb6531b08cdc78e3623bb8a  pig-v1.3.3.darwin-arm64.tar.gz
d18a92f9aa05d6315c5e9bfde3245afc08fca93d200a8063aa20cb40feb8e85e  pig-v1.3.3.linux-amd64.tar.gz
62d020072360229b47f6c430b014344b912f2d9b58fd528154ae9c4ee805190a  pig-v1.3.3.linux-arm64.tar.gz
7a613a1f1c323ee78276b1733df026b8b0f415e0057b4cb8e509f771bfd3d614  pig_1.3.3-1_amd64.deb
f4c91ce86b787b6ab8cd584949d38c2ca87eb82d5e066bab91b80345252f43d8  pig_1.3.3-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.3.3
