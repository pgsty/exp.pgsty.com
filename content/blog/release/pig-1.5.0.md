---
title: "pig v1.5.0"
linkTitle: "v1.5.0"
date: 2026-07-04
author: "Ruohang Feng"
description: "531 extensions, pigsty v4.4, pg/pt/pb/pitr rework, clone & fork"
categories: [release]
tags: [Release, pig]
weight: 40
---

Pig `v1.5.0` is a PostgreSQL operations release for day-to-day DBA work. It adds local database clone/fork workflows, clarifies the boundaries between `pg`, `pt`, `pb`, and `pitr`, and tightens preview, confirmation, and structured-output behavior for high-risk operations.

## Highlights

- `pig pg` is now more focused on local PostgreSQL operations. `pig pg clone` creates quick database-level copies, while `pig pg fork` creates disposable physical instance forks for local validation, recovery drills, and isolated experiments.
- Recovery flows are split more clearly: `pig pitr` is the orchestration entry point across Patroni, PostgreSQL, and pgBackRest; `pig pb restore` remains the low-level pgBackRest restore primitive. Restore commands now require an explicit target and provide more concrete plans and post-restore guidance.
- Patroni operations are more predictable: high-risk actions such as `pig pt restart`, `reinit`, `switchover`, and `failover` use Pig-managed confirmation and plan output; `pig pt config pg` points operators to `pig pt restart --pending` when a restart is required.
- Automation is safer: structured output no longer implies confirmation for destructive commands. High-risk execution requires explicit `-y/--yes`, while `--plan` and `next_actions` are more consistent for preview-then-execute workflows.
- Logs and status output are more useful during incidents: `pg`, `pb`, and `pt` log commands now cover common latest / tail / show / grep workflows, and structured log snapshots use JSONL semantics.
- Build and release defaults were refreshed: Pig is `1.5.0`, embedded Pigsty is `4.4.0`, and `pig build pgrx` defaults to `cargo-pgrx 0.19.1`.

## Extension Catalog

- Available extensions: **524 -> 531**, with no removals.
- New extensions: `pg_ducklake`, `pgdisablelogerror`, `pg_stat_log`, `pg_stat_plans`, `passwordpolicy`, `db2fce`, `plpgsql_wrap`.
- Refreshed a batch of existing extension versions and package metadata, including `timescaledb 2.28.2`, `postgis 3.6.4`, `vector 0.8.4`, `biscuit 2.4.1`, `citus 14.1.0`, `orioledb 1.8`, `documentdb 0.113`, `credcheck 5.0`, and `pgtt 4.5`.
- `orioledb` aliases no longer pin to PG17; they resolve against the requested PostgreSQL major. EL9 ARM64 Patroni aliases now point to noarch packages.

## Compatibility Notes

- Use `-y/--yes` for destructive operations in automation; structured output mode no longer substitutes for human confirmation.
- `pig pb restore` and `pig pitr` require exactly one explicit recovery target; use `--target-action=promote` for auto-promote behavior.
- Several ambiguous short options were cleaned up. For log commands, `-o json` means a JSONL snapshot and is not used for tail/follow streaming modes.

## Checksums

```bash
9f83b78ed2eccedd55a86c634f88364f1945c3cefa1b23efdd72a7cf2062e1df  pig-1.5.0-1.aarch64.rpm
b792001498e9907d4659db46640f9c5164152b20689f90f93418f76fb4633e6e  pig-1.5.0-1.x86_64.rpm
ae1081dfbff8564ecdf713c85e8025c91bfd38e6575ea9ac99a92f968ab8a29d  pig-v1.5.0.darwin-amd64.tar.gz
6d69efcdcdc79fd90d2112e1e8042887020402aa037252d89d632243e7085dc6  pig-v1.5.0.darwin-arm64.tar.gz
8f914821b317cde73d3aec4ed311d5e90710bbc8cb372c1de3322083c31f4a85  pig-v1.5.0.linux-amd64.tar.gz
d4de9ef1c28d0a3661c4a4d47c469b7bfd5f5bddb610325796afb669ab162234  pig-v1.5.0.linux-arm64.tar.gz
35fd32affb4cb5bcca845d47a768782fb7005f06fcc1bcb5b7755d2627f96245  pig_1.5.0-1_amd64.deb
2be1df804d3f630560bc3ced0107c49ffad8bb52b004f72c7f8b4d09dc8d3e04  pig_1.5.0-1_arm64.deb
```

Release: https://github.com/pgsty/pig/releases/tag/v1.5.0
