---
title: "pig v1.2.0"
linkTitle: "v1.2.0"
date: 2026-02-23
author: "Ruohang Feng"
description: "Unified aliases, routine updates, plan mode, repo fixes"
categories: [release]
tags: [Release, pig]
weight: 130
---

- Extension catalog and alias resolution enhancements:
  - Introduce dynamic PG category alias resolution by PG major version.
  - Add OS-level alias overrides (`ansible`/`bootstrap`) and converge unknown distro fallback to PGDG-only.
  - Add aliases such as `node/infra` and `babelfish/cloudberry`, and refresh extension metadata to reduce package resolution ambiguity.
- Plan preview for high-risk operations:
  - Add `pig install --plan` with structured execution plan output.
  - Align preview semantics for `pig pitr` and pgBackRest `repack/expire` under `--plan` / `--dry-run`.
  - Add plan-flag consistency tests to keep subcommand behavior aligned.
- Native `sty` configuration capability:
  - Add `pig sty configure` with full execution flow (preflight, argument handling, execution orchestration).
  - Unify `sty conf/configure` behavior: native implementation by default, with `--raw` fallback retained.
  - Add tests for configure main flow, preflight, routing, and install integration to improve maintainability.
- Repo/build/reliability fixes:
  - Fix nil dereference in repo cache on `os.Stat` error paths.
  - Align Ubuntu and Debian repo channel mapping, and add timeout control for mirror pulls during reload.
  - Harden `repo rm` for dotted module names with safe deletion and path validation.
  - Fix symlink preservation, cross-device migration, and target-directory handling in `sty init` and build flows.
  - Improve text output and matrix color rendering, and fix ext command validation for empty args/targets.

- 35 commits, 66 files changed, LOC: `+5006 / -379`

- **PG extension and kernel package updates**

| Package             | Old      | New      | Notes                                             |
|:--------------------|:---------|:---------|:--------------------------------------------------|
| `timescaledb`       | 2.25.0   | 2.25.1   |                                                   |
| `citus`             | 14.0.0-3 | 14.0.0-4 | Rebuilt from the latest official upstream release |
| `age`               | 1.7.0    | 1.7.0    | Add PG 17 support for version 1.7.0               |
| `pg_background`     | -        | 1.8      | DEB-only build; RPM package comes from PGDG       |
| `pgmq`              | 1.10.0   | 1.10.1   | This extension package is currently unavailable   |
| `pg_search`         | 0.21.6   | 0.21.8   | Used as direct download package                   |
| `oriolepg`          | 17.11    | 17.16    | OriolePG kernel update                            |
| `orioledb`          | beta12   | beta14   | Matched with OriolePG 17.16                       |
| `cloudberry`        | -        | 2.0.0    | New package                                       |
| `babelfishpg`       | -        | 5.5.0    | New BabelfishPG package group                     |
| `babelfish`         | -        | 5.5.0    | New Babelfish compatibility package               |
| `antlr4-runtime413` | -        | 4.13     | New runtime dependency for Babelfish              |


## Checksums

```bash
344b77385fa9c3d4fe5e1961340e68716251e38d1cb8308f5af45ce8a03cd206  pig-1.2.0-1.aarch64.rpm
aa9cf1820a9045cc42f0d66689d5e8679cb71452042f3f01ddd4c3a518a2b757  pig-1.2.0-1.x86_64.rpm
f26e4d9e9fa76c39f7c591c18a09287ca3388e016d121c196302ee9eafb5b678  pig-v1.2.0.darwin-amd64.tar.gz
2ca41efc3495822305f6e6a3ae1825d57cc97e764f280581f833c72e6e5019a2  pig-v1.2.0.darwin-arm64.tar.gz
f7aa291b3534d92d0459b6e8301190e39c63db14a45a6c097d4c5d3062c35181  pig-v1.2.0.linux-amd64.tar.gz
38007ecd6d7a69bae0e3d8f7c78f1a4c8bbaead320b7ac319b0d94d6b53853f0  pig-v1.2.0.linux-arm64.tar.gz
e824716ddfbf3805dc0a1fd6d97917241b7780503657e9fd40a37beb6b398d7a  pig_1.2.0-1_amd64.deb
b67baa404d877b37004331041cb270c85b8f9a3f8a92a5083390a54d76553d2a  pig_1.2.0-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.2.0
