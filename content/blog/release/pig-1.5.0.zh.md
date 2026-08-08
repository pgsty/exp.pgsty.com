---
title: "pig v1.5.0"
linkTitle: "v1.5.0"
date: 2026-07-04
author: "冯若航"
description: "531 个扩展，pigsty v4.4，pg/pb/pt/pitr 重做，clone/fork"
categories: [release]
tags: [Release, pig]
weight: 40
---

Pig `v1.5.0` 是一次面向 PostgreSQL 日常运维的版本：新增本地数据库 clone / fork 工作流，明确 `pg`、`pt`、`pb`、`pitr` 的职责边界，并收紧高风险操作的预览、确认与结构化输出行为。

## 主要变化

- `pig pg` 更聚焦本地 PostgreSQL 操作。新增 `pig pg clone` 用于快速创建数据库级副本，新增 `pig pg fork` 用于创建一次性物理实例分叉，适合本地验证、恢复演练和隔离实验。
- 恢复流程拆得更清楚：`pig pitr` 作为 Patroni / PostgreSQL / pgBackRest 的恢复编排入口；`pig pb restore` 保持为低层 pgBackRest restore 原语。恢复命令现在必须指定明确目标，并提供更具体的 plan 与恢复后指引。
- Patroni 操作更可预期：`pig pt restart`、`reinit`、`switchover`、`failover` 等高风险操作统一由 Pig 负责确认与 plan 输出；`pig pt config pg` 会提示是否需要 `pig pt restart --pending`。
- 自动化脚本更安全：结构化输出不再隐式确认破坏性操作，执行高风险动作需要显式 `-y/--yes`；`--plan` 与 `next_actions` 更一致，方便先预览、再执行。
- 日志与状态输出更适合排障：`pg`、`pb`、`pt` 的日志命令补齐 latest / tail / show / grep 等常用入口，结构化日志快照使用 JSONL 语义。
- 构建与发布默认值更新：Pig 版本为 `1.5.0`，内置 Pigsty 版本为 `4.4.0`，`pig build pgrx` 默认 `cargo-pgrx` 升级到 `0.19.1`。

## 扩展目录

- 可用扩展数量从 **524** 增加到 **531**，没有移除项。
- 新增扩展：`pg_ducklake`、`pgdisablelogerror`、`pg_stat_log`、`pg_stat_plans`、`passwordpolicy`、`db2fce`、`plpgsql_wrap`。
- 刷新一批已有扩展版本与包元数据，代表性更新包括 `timescaledb 2.28.2`、`postgis 3.6.4`、`vector 0.8.4`、`biscuit 2.4.1`、`citus 14.1.0`、`orioledb 1.8`、`documentdb 0.113`、`credcheck 5.0`、`pgtt 4.5`。
- `orioledb` alias 不再固定到 PG17，而是按请求的 PostgreSQL 主版本解析；EL9 ARM64 Patroni alias 也调整为 noarch 包。

## 兼容性提醒

- 自动化执行破坏性操作时请使用 `-y/--yes`；结构化输出模式不会再替代人工确认。
- `pig pb restore` / `pig pitr` 需要明确指定一个恢复目标；自动 promote 类行为请使用 `--target-action=promote`。
- 若干易混淆短参数经过整理；日志命令的 `-o json` 表示 JSONL 快照，不用于 tail / follow 这类流式交互场景。


## 校验和

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

发布：https://github.com/pgsty/pig/releases/tag/v1.5.0
