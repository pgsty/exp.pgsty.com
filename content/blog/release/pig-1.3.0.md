---
title: "pig v1.3.0"
linkTitle: "v1.3.0"
date: 2026-02-27
author: "Ruohang Feng"
description: "Build pipeline hardening, 461 extensions, new pgedge/ivory support"
categories: [release]
tags: [Release, pig]
weight: 120
---

This release is a focused engineering update from `v1.2.0` to `v1.3.0`: 15 commits, 74 files changed, `+1184 / -236` LOC.

It hardens the `pig build` pipeline and extends catalog/alias coverage, increasing total extensions from **451** to **461**.

## Highlights

- Build source download improvements (`pig build get`):
  - Parse multi-source `Source` fields (whitespace/newline/tab) and deduplicate entries.
  - Add source mappings for `agensgraph` / `agentsgraph`.
  - `pgedge` now downloads both `postgresql-17.9.tar.gz` and `spock-5.0.5.tar.gz`.
- Dependency resolution and install improvements (`pig build dep`):
  - RPM dependencies can infer PG major from `pgmajorversion` in spec files; missing spec/control files now return explicit errors.
  - DEB dependency parsing now covers `Build-Depends` / `Build-Depends-Arch` / `Build-Depends-Indep`, including multiline fields, alternatives, arch qualifiers, and build-profile cleanup.
  - `PGVERSION` placeholders can be expanded from `--pg`, installed PG majors, or extension metadata.
  - Dependency install failures are downgraded to warnings so batch runs continue.
- DEB build result semantics fixed (`pig build ext/pkg`):
  - Successful build command exit code is authoritative; artifact discovery is best-effort warning only.
  - Suppress empty package-list banners on successful no-artifact runs.
  - Partial artifacts are warnings, not failures.
  - Build logs now print real metadata source/version values instead of always composing `name-version`.
- Better machine-readable ext operation output (`pig ext rm/update`):
  - After alias resolution, `removed/updated` now returns resolved package names instead of extension aliases.
- Extension catalog and alias updates:
  - New aliases: `agensgraph` / `agens`, `pgedge`, `babelfishpg`.
  - `openhalodb` is aligned to PG14 package naming; `ivorysqldb` naming is aligned.
  - Fork metadata and availability matrix were refreshed in batch (including `timescaledb`, `pgmq`, `orioledb`, `documentdb`, `pg_tde`, and `babelfishpg_*` entries).
- Engineering and release:
  - Version bumped to `v1.3.0` (including a `v1.2.1` transition commit), copyright year moved to 2026, and README refreshed for 461 extensions and current alias docs.

## Compatibility Notes

- Structured `removed/updated` fields in `pig ext rm/update` now contain package names. Automation that matched extension aliases should update parsing logic.

## New Extensions (451 -> 461)

| Extension             | Version | Notes                                             |
|:----------------------|:--------|:--------------------------------------------------|
| `aux_mysql`           | 1.5     | openHalo MySQL compatibility helper (PG14)        |
| `gb18030_2022`        | 1.0     | IvorySQL charset conversion module                |
| `ivorysql_ora`        | 1.0     | IvorySQL Oracle compatibility extension           |
| `ora_btree_gin`       | 1.0     | Oracle datatype GIN indexing support              |
| `ora_btree_gist`      | 1.0     | Oracle datatype GiST indexing support             |
| `pg_get_functiondef`  | 1.0     | Function definition utility                        |
| `plisql`              | 1.0     | PL/iSQL procedural language                        |
| `snowflake`           | 2.4     | pgEdge Snowflake-style ID generator                |
| `spock`               | 5.0.5   | pgEdge multi-master logical replication extension  |
| `lolor`               | 1.2.2   | pgEdge logical-replication-friendly large objects  |

## Full Commit List (`v1.2.0..v1.3.0`)

- `b8ecf8d` bump version string to 1.2.1
- `55df9a4` build/get: support multi-source parsing and pgedge spock tarball
- `da8e347` add agensgraph and pgedge alias
- `86edbd7` ext: show resolved package names in rm/update results
- `ef3c905` build/dep: improve rpm/deb dependency resolution
- `7144e09` ext/catalog: refresh fork metadata and matrix entries
- `befffbf` build(deb): treat successful build command as authoritative result
- `33fd517` build(deb): avoid empty package list banner on successful no-artifact runs
- `3b450f2` avoid concat ext pkg name with version when download
- `33847ab` fix(ext): satisfy staticcheck S1011 in rm/update
- `b8b917d` build(dep): treat dependency install failures as warnings
- `8110c00` adjust ivorysqldb babelfishpg alias
- `fac9faf` bump version to 1.3.0
- `1f88f06` chore: update copyright year to 2026
- `c804757` v1.3.0

## Checksums

```bash
e8409cc8165139028323094bebede495d4b0d0a52616d1aecd8c7ecd3fb7471d  pig-1.3.0-1.aarch64.rpm
73645ea4b9ce27b44b2c7f4587e6218cdbbba045f32dd45c942e03cf9020c61e  pig-1.3.0-1.x86_64.rpm
a2d8a14b11606f4a23ca7b929686ff020fc8ce29e7cec21074f710f981aee6d4  pig-v1.3.0.darwin-amd64.tar.gz
fffb94bfc1808b45d8bef3fb63783c1a8e78057e0315ab5b8752088e2c9a555f  pig-v1.3.0.darwin-arm64.tar.gz
27220509c22d26eb8821ac189b1de9c4745adc0a0d91719df7d0b1fc1176b765  pig-v1.3.0.linux-amd64.tar.gz
d124450333e61a5c7d0ed387b13b4087cfd2a81a3fde018232e6bf9b4db6ba0e  pig-v1.3.0.linux-arm64.tar.gz
54f3e0561286b3c0af122137fd475213eff54bc82c69b8b46d1148112ab45b80  pig_1.3.0-1_amd64.deb
beb8ff31d1e64dbfcf6896115e6d200d835fc28bbac5a5b92d75096ef1e68c80  pig_1.3.0-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.3.0
