---
title: "pig v1.4.2"
linkTitle: "v1.4.2"
date: 2026-06-18
author: "Ruohang Feng"
description: "524 extensions, PG19 beta, pgrx 0.18.1, Patroni fixes"
categories: [release]
tags: [Release, pig]
weight: 50
---

- Refresh the built-in extension catalog from **510** to **524** available extensions. This adds 14 extensions: `pg_stl`, `pgmnemo`, `psql_bm25s`, `pg_orca`, `pg_sorted_heap`, `graph`, `pgrdf`, `fsm_core`, `jsonschema`, `pg_durable`, `pg_mockable`, `pg_uuid_v8`, `pg_stat_backtrace`, and `pg_projection`.
- Update package metadata for 48 existing extensions, including `timescaledb 2.28.0`, `timescaledb_toolkit 1.23.0`, `pg_task 2.1.29`, `pg_search 0.24.0`, `pg_clickhouse 0.3.2`, `pg_graphql 1.6.1`, `documentdb 0.112`, `toastinfo 1.7`, `wrappers 0.6.1`, and `pgclone 4.3.2`. No extensions were removed or demoted.
- Add PostgreSQL 19 beta install/build/config support. PG19 is accepted as an explicit installable major, while PostgreSQL 18 remains the stable default for auto-detection, catalog display, and latest-version aliases.
- Add `pg19` package aliases and PG19 category alias resolution. PG19 category aliases borrow the PostgreSQL 18 visibility template and limit beta package expansion to PGDG-origin entries.
- Teach `pig sty conf -v 19` to enable the `beta` repository module when the template supports it, and emit clear warnings when a template is not tuned for PG19 beta or cannot enable the beta repo automatically.
- Fix Patroni cluster operations by passing the resolved `CLUSTER_NAME` to `patronictl restart`, `reinit`, `switchover`, and `failover`; `pig pt list` also accepts an optional cluster name.
- Bump the default `pgrx` version for `pig build pgrx` from `0.18.0` to `0.18.1`.
- Bump release metadata to `v1.4.2`, refresh Go module checksums, and add focused tests for PG19 aliases/config generation plus Patroni cluster-scope behavior.

## Checksums

```bash
790afe4d6622cb041b06c622bc466cb1b2960a77487f368238027fb4a3a5ef93  pig-1.4.2-1.aarch64.rpm
ef918166b38a5eb1d108a928718c9e2cb8c3590e5a1f72effee942faca9b4bea  pig-1.4.2-1.x86_64.rpm
3e37ff22aed076cbdd453911dc89fcc9340b1a4faac62c0580094bc1eb2d6273  pig-v1.4.2.darwin-amd64.tar.gz
5eb7db776cb149331ebb33e3e6164e1cf711d0107941b92c6930a1d4c4b4eb23  pig-v1.4.2.darwin-arm64.tar.gz
c536c324e40a861217e31f4699ee5f0e6c2daeb4e6f0f0e8cc5f606da9d787eb  pig-v1.4.2.linux-amd64.tar.gz
8b2d5746264a95269535e5a426f78fe0020f73fa3391fcb613f274551c4786ab  pig-v1.4.2.linux-arm64.tar.gz
566e06f6da1fe9d635c41258d20cd9ff10de4e6e74b3b41ba2c6204ba22743c8  pig_1.4.2-1_amd64.deb
8c09e741975cb2f74b0f88c5995a8fa43d6c30a9a7ab7aaf0b8d83a7c66e1fc1  pig_1.4.2-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.4.2
