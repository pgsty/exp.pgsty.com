---
title: "pig v1.6.0"
linkTitle: "v1.6.0"
date: 2026-07-28
author: "冯若航"
description: "562 个已打包扩展，pt 原生透传，inventory 与 CMDB，Grafana 管理"
categories: [release]
tags: [Release, pig]
weight: 20
---

Pig `v1.6.0` 是一个大版本：`pig pt` 重写为 `patronictl` 原生透传，新增根级 `pig inventory` 命令组提供 `pigsty.yml` 的无损编辑与校验（附带实验性的 PostgreSQL CMDB 交换能力），`pig sty grafana` 提供原生 Grafana 仪表盘管理，已打包扩展目录增至 562 个。

## 主要变化

- `pig pt` 重写为 `patronictl` 原生透传：所有集群命令（`list`、`restart`、`switchover`、`failover`、`edit-config` 等）直接转发，使用原生参数、交互确认、输出与退出码，patronictl 的新功能无需等待 pig 发版即可使用。本地保留 `status`、`log`、`set`、`service/svc` 辅助命令，新增 `-c/--config-file`、`-d/--dcs-url`、`-k/--insecure` 选项与 `pig pt -- …` 逃逸写法。
- 新增根级 `pig inventory` 命令组（别名 `inv`）：`status` / `list` / `show` / `edit` / `validate` / `check` / `diff` —— 无损 YAML 引擎逐字节保留注释、格式、键序与锚点；`edit` 先校验再原子写入，非法 YAML 不可能落盘。
- 新增**实验性** `pig inventory cmdb` 子命令（`check` / `init` / `load` / `dump` / `enable` / `disable`），通过原生驱动与 Pigsty 的 PostgreSQL CMDB 交换配置清单，破坏性操作带超时限界与摘要锁定的确认门。
- 新增 `pig sty grafana`（别名 `gf`）通过 HTTP 原生管理 Grafana 仪表盘：`info` / `list` / `boot` / `load` / `init` / `dump` / `clean` / `lang` / `style`。`pig sty` 命令面简化：移除 `sty edit` / `validate` / `check` / `cmdb` / `dashboard` / `release`，改用 `pig inventory`、`pig sty grafana` 与 `pig sty list` / `get`。
- 可靠性强化：仓库 / 目录 / 下载写入全部原子化（中断不再留下半截文件）；结构化输出 `-o json|yaml` 下 stdout 只包含结果信封，被包裹命令的输出走 stderr；退出码更精确（用法错误 → 2，缺少 `--yes` 确认 → 7）；Ansible 列表变量改用 JSON 编码防注入。
- 仓库刷新：MySQL 仓库升级到 8.4 LTS，新增 Percona XtraBackup（`pxb84`）与 MySQL Tools 仓库，Kubernetes 升级到 v1.36，LLVM apt 覆盖 Debian/Ubuntu 26，Percona TDE 改用 repo.percona.com 官方源，移除 `wiltondb` 仓库。
- 工具链：Go 1.26.5，新增原生 PostgreSQL 驱动（pgx v5），内置 Pigsty 版本 `4.4.0`。

## 扩展目录

- 已打包扩展数量从 **531** 增加到 **562**；PGEXT.CLOUD 总目录收录 **2230** 个扩展。
- 新增 33 个扩展，包括 `pg_lake` 家族（`pg_lake`、`pg_lake_table`、`pg_lake_engine`、`pg_lake_iceberg`、`pg_lake_copy`）、`pg_jieba`、`pg_cjk_parser`、`pg_fts`、`pgmonitor`、`pgmemento`、`pg_tiktoken_c`、`online_advisor`、`pgsqlmock`、`plx` 等。
- 移除 2 个：`pg_analytics`、`spat`；刷新 58 个扩展版本，包括 `vector 0.8.5`、`timescaledb 2.28.3`、`pg_search 0.24.3`、`pg_tde 2.2.1`、`powa 5.2.0`。
- 包别名与 Pigsty 同步：`kafka` 更名为 `kafka-stack`；Debian/Ubuntu 的 `postgresql` 别名收窄为仅 `postgresql-$v`（完整开发套件请用 `pgsql` / `pgsql-full`）。

## 兼容性提醒

- ⚠ `pig pt failover <name>`：位置参数现在是**集群名**而不是晋升候选成员 —— 请改用 `pig pt failover CLUSTER --candidate MEMBER`，升级前务必检查 failover 自动化脚本。
- `pig pt` 位置参数改为原生的集群优先形式（`restart CLUSTER [MEMBER]`）；转发命令返回 patronictl 原生退出码、由 patronictl 自行交互确认（`-y` 不再门禁这些命令），且不再支持 `-o json`（请改用原生 `--format json`）。`pig pt config` 由 `pig pt set K=V` 与原生 `show-config` / `edit-config` 取代。
- 结构化输出模式下，被包裹工具的输出移至 stderr，stdout 只有 JSON/YAML 信封 —— 请更新解析混合输出的脚本。
- `pig inventory edit` 编辑成功后会将配置文件权限收紧为 0600（文件可能包含数据库凭据）。

## 校验和

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

发布：https://github.com/pgsty/pig/releases/tag/v1.6.0
