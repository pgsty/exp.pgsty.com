---
title: "pig v1.1.0"
linkTitle: "v1.1.0"
date: 2026-02-12
author: "Ruohang Feng"
description: "451 extensions, Agent-Native CLI framework"
categories: [release]
tags: [Release, pig]
weight: 140
---

This version is a planned architecture-level upgrade from `v1.0.0` to `v1.1.0` (79 commits, 193 files changed),
with the core goal of moving pig from a "human-friendly CLI" to an "agent-native orchestratable CLI".

Seven new extensions are added, bringing the total available extensions to 451.

## New Features

- Land the unified agent-native output framework: introduce global `--output` (`text/yaml/json/json-pretty`), and provide unified `Result` structure, stable status codes, and machine-readable output for `ext/repo/pg/pt/pb/pitr/status/version/context`.
- Introduce ANCS (Agent Native Command Schema) metadata: add semantic fields such as `type/volatility/parallel/risk/confirm/os_user/cost`, and make `help` emit a command capability tree directly in structured mode for agent-side capability and risk discovery.
- Add `pig context` (`pig ctx`) environment snapshot command: aggregate host, PostgreSQL, Patroni, pgBackRest, and extension information in one call for direct agent workflow context injection.
- Expand plan capabilities beyond PITR: add `pig ext add/rm --plan`, `pig pg stop/restart --plan`, `pig pt switchover/failover --plan`, and align with `pig pitr --plan/--dry-run` into a reviewable execution plan format (actions, scope, risks, expected outcomes).
- Further improve structured result coverage: embed native `pgbackrest info` JSON, and unify structured return DTOs across Patroni/PostgreSQL/PITR/Repo/Ext subsystems for automation compatibility.
- Strengthen compatibility layer: add legacy structured wrappers for existing command groups such as `pg_exporter/pg_probe/do/sty`, preserving legacy interaction behavior while exposing structured execution results and output capture.
- Update pigsty to `v4.1.0`.

## Extension Update

| Extension          | Old          | New           |
|:-------------------|:-------------|:--------------|
| timescaledb        | 2.24.0       | 2.25.0        |
| citus              | 14.0.0-2     | 14.0.0-3      |
| pg_incremental     | 1.2.0        | 1.4.1         |
| pg_bigm            | 1.2-20240606 | 1.2-20250903  |
| pg_net             | 0.20.0       | 0.20.2        |
| pgmq               | 1.9.0        | 1.10.0        |
| pg_textsearch      | 0.4.0        | 0.5.0         |
| pljs               | 1.0.4        | 1.0.5         |
| sslutils           | 1.4-1        | 1.4-2         |
| table_version      | 1.11.0       | 1.11.1        |
| supautils          | 3.0.2        | 3.1.0         |
| pg_math            | 1.0          | 1.1.0         |
| pgsentinel         | 1.3.1        | 1.4.0         |
| pg_uri             | 1.20151224   | 1.20251029    |
| pgcollection       | 1.1.0        | 1.1.1         |
| pg_readonly        | 1.0.3        | 1.0.4         |
| timestamp9         | 1.4.0-1      | 1.4.0-2       |
| pg_uint128         | 1.1.1        | 1.2.0         |
| pg_roaringbitmap   | 0.5.5        | 1.1.0         |
| plprql             | 18.0.0       | 18.0.1        |
| pglinter           | 1.0.1        | 1.1.0         |
| pg_jsonschema      | 0.3.3        | 0.3.4         |
| pg_anon            | 2.5.1        | 3.0.1         |
| vchord             | 1.0.0        | 1.1.0         |
| pg_search          | 0.21.4       | 0.21.6/0.21.7 |
| pg_graphql         | 1.5.12-1     | 1.5.12-2      |
| pg_summarize       | 0.0.1-2      | 0.0.1-3       |
| nominatim_fdw      | -            | 1.1.0         |
| pg_utl_smtp        | -            | 1.0.0         |
| pg_strict          | -            | 1.0.2         |
| pg_track_optimizer | -            | 0.9.1         |
| pgmb               | -            | 1.0.0         |

## Bug Fixes

- Security fix: resolve parsing panic in `pig build proxy` when receiving malformed proxy addresses.
- Security fix: resolve path traversal risk in `pig pg log`, preventing access to files outside the log directory via `../../`.
- Security hardening: improve installer/repo path and quoting handling to reduce path injection and invalid-path misuse risks.
- Build pipeline reliability fixes: correctly propagate errors and return non-zero exit codes in `pig build get/pkg/ext` when download/build fails; fix false failures in DEB builds caused by `pg_ver` mismatch.
- Repo/catalog refresh fixes: support quiet mirror fallback for `ext/repo reload`; make `repo add/set/rm` return proper error status when cache updates fail.
- Extension management fixes: adjust `ext update` to explicit-target updates and fix status drift issues; ensure `ext import` downloads requested DEB resources to the specified repo directory.
- Output/observability fixes: align structured output exit code behavior with text mode rendering; improve permission handling and parsing stability in `pg status`.

## Checksums

```bash
95245dc035270df2b02cdd5d19afac57ccf4949a61b07b1b806fffde3a3b780e  pig-1.1.0-1.aarch64.rpm
8b1a26f1b5dd002841a0b31904eea8ce94d1e6c4acde4704a78d9e121e1656f4  pig-1.1.0-1.x86_64.rpm
dbd079510513f1cd0521b0871cc6fe3eed8f7fa26f66c04c682568c43e24c456  pig-v1.1.0.darwin-amd64.tar.gz
3f3ba081b54569a7de4d9a8fce72c02c84d9e1cbeb53173567f970c7291af251  pig-v1.1.0.darwin-arm64.tar.gz
ad61384bf01cbb8346ce869da0bc893203ad316c516fb9420cb748f1519a005e  pig-v1.1.0.linux-amd64.tar.gz
7713632beea1e6ca5c3e2e7172c4adee13a2b1b256755f6c2898b6ca98ee1e00  pig-v1.1.0.linux-arm64.tar.gz
70cfc41b7b0aad48f29e12c22c34afd55b938bf50868ac8ab067b9cb62ccb867  pig_1.1.0-1_amd64.deb
fc5cf16671254f8f3495ff7e80c9d77d06b2328c1a247f90f96cf1e918e0ad0e  pig_1.1.0-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.1.0
