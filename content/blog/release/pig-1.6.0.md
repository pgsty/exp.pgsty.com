---
title: "pig v1.6.0"
linkTitle: "v1.6.0"
date: 2026-07-28
author: "Ruohang Feng"
description: "562 packaged extensions, patronictl passthrough, inventory & CMDB, Grafana"
categories: [release]
tags: [Release, pig]
weight: 20
---

Pig `v1.6.0` is a major release: `pig pt` becomes a transparent `patronictl` launcher, the new root-level `pig inventory` command group brings lossless editing and validation of `pigsty.yml` (with an experimental PostgreSQL CMDB bridge), `pig sty grafana` adds native Grafana dashboard management, and the packaged extension catalog grows to 562.

## Highlights

- `pig pt` is rewritten as a native `patronictl` passthrough: all cluster commands (`list`, `restart`, `switchover`, `failover`, `edit-config`, …) forward directly with native flags, prompts, output, and exit codes, so new patronictl features work without waiting for a pig release. Local helpers `status`, `log`, `set`, and `service/svc` remain, with new `-c/--config-file`, `-d/--dcs-url`, `-k/--insecure` options and a `pig pt -- …` escape hatch.
- New root-level `pig inventory` command group (alias `inv`): `status` / `list` / `show` / `edit` / `validate` / `check` / `diff` — a lossless YAML engine that preserves comments, formatting, key order, and anchors byte-for-byte; `edit` validates before writing and writes atomically, so invalid YAML can never reach disk.
- New **experimental** `pig inventory cmdb` subcommands (`check` / `init` / `load` / `dump` / `enable` / `disable`) exchange the inventory with the Pigsty CMDB in PostgreSQL over a native driver, with bounded timeouts and digest-pinned confirmation for destructive operations.
- New `pig sty grafana` (alias `gf`) manages Grafana dashboards natively over HTTP: `info` / `list` / `boot` / `load` / `init` / `dump` / `clean` / `lang` / `style`. The `pig sty` surface is simplified: `sty edit` / `validate` / `check` / `cmdb` / `dashboard` / `release` are removed in favor of `pig inventory`, `pig sty grafana`, and `pig sty list` / `get`.
- Reliability hardening: repo / catalog / download writes are atomic (no more truncated files on interrupt); structured `-o json|yaml` keeps stdout as a pure result envelope with wrapped-tool output on stderr; finer exit codes (usage errors → 2, missing `--yes` confirmation → 7); Ansible list variables are JSON-encoded.
- Repository refresh: MySQL repos upgraded to 8.4 LTS, new Percona XtraBackup (`pxb84`) and MySQL Tools repos, Kubernetes v1.36, LLVM apt coverage for Debian/Ubuntu 26, Percona TDE sourced directly from repo.percona.com, `wiltondb` repo removed.
- Toolchain: Go 1.26.5, new native PostgreSQL driver (pgx v5), embedded Pigsty version `4.4.0`.

## Extension Catalog

- Packaged extensions: **531 -> 562**; the broader PGEXT.CLOUD directory contains **2,230** entries.
- 33 new extensions, including the `pg_lake` family (`pg_lake`, `pg_lake_table`, `pg_lake_engine`, `pg_lake_iceberg`, `pg_lake_copy`), `pg_jieba`, `pg_cjk_parser`, `pg_fts`, `pgmonitor`, `pgmemento`, `pg_tiktoken_c`, `online_advisor`, `pgsqlmock`, and `plx`.
- 2 removed: `pg_analytics`, `spat`; 58 version refreshes, including `vector 0.8.5`, `timescaledb 2.28.3`, `pg_search 0.24.3`, `pg_tde 2.2.1`, and `powa 5.2.0`.
- Package aliases synced with Pigsty: `kafka` is renamed to `kafka-stack`; the Debian/Ubuntu `postgresql` alias now maps to `postgresql-$v` only (use `pgsql` / `pgsql-full` for the full dev set).

## Compatibility Notes

- ⚠ `pig pt failover <name>`: the positional argument is now the **cluster**, not the promotion candidate — use `pig pt failover CLUSTER --candidate MEMBER` and review any failover automation before upgrading.
- `pig pt` positionals are native cluster-first (`restart CLUSTER [MEMBER]`); forwarded commands return native patronictl exit codes, own their confirmation prompts (`-y` no longer gates them), and no longer support `-o json` (use native `--format json`). `pig pt config` is replaced by `pig pt set K=V` and native `show-config` / `edit-config`.
- In structured output mode, wrapped-tool output moves to stderr and stdout carries only the JSON/YAML envelope — update scripts that parsed mixed output.
- `pig inventory edit` tightens the inventory file mode to 0600 after a successful edit, since the file may contain credentials.

## Checksums

```bash
6899e8a3e1c0adfe8c0c177c0632b0a00821b304ed5998fcbdf28d02660c6768  pig-1.6.0-1.aarch64.rpm
cabe593fe7f5c31cdbcd8d546ae4925b57f98f70c564452335568389f3f9737c  pig-1.6.0-1.x86_64.rpm
1f46d4a0b4710eed06b2cf8e7e17ee04b8d65331697c5c65afd513cc28282231  pig-v1.6.0.darwin-amd64.tar.gz
845decb95697fc68bc5e12bc80cecfd4c6d23160afee96568b699d82f2e9261d  pig-v1.6.0.darwin-arm64.tar.gz
4f1bb4fda8131db9f40db15e1575a6045b373dee609250cf5ee2bdedc2db89e2  pig-v1.6.0.linux-amd64.tar.gz
4384d11150e31d614ed4ac3de4d6bf7ee7fa111ac84f5575753bb9f2f31f4ed8  pig-v1.6.0.linux-arm64.tar.gz
e35ef0f2c76afe5f3512d34c0440abd8c0106c0e2775c5452e167ae3a4127e8e  pig_1.6.0-1_amd64.deb
c3bc6d04c6acd7e5c3164a33b7525b25a93e2de9822ce957c15c18ee0d551901  pig_1.6.0-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.6.0
