---
title: "pig v1.1.0"
linkTitle: "v1.1.0"
date: 2026-02-12
author: "冯若航"
description: "451 扩展，Agent-Native CLI 框架"
categories: [release]
tags: [Release, pig]
weight: 140
---

该版本是从 `v1.0.0` 到 `v1.1.0` 的一次规划中架构级升级（79 commits，193 files 变更），
核心目标是把 pig 从“人类可用 CLI”推进到“Agent-native 可编排 CLI”。

新增七个扩展，总可用扩展数量达到 451 个。

## 新功能

- Agent-native 统一输出框架落地：引入全局 `--output`（`text/yaml/json/json-pretty`），为 `ext/repo/pg/pt/pb/pitr/status/version/context` 等命令提供统一 `Result` 结构、稳定状态码与可机器解析输出。
- 引入 ANCS（Agent Native Command Schema）元数据体系：为命令补齐 `type/volatility/parallel/risk/confirm/os_user/cost` 等语义字段，`help` 在结构化模式下可直接输出命令能力树，便于 Agent 自动发现能力与风险边界。
- 新增 `pig context`（`pig ctx`）环境快照命令：一次调用聚合主机、PostgreSQL、Patroni、pgBackRest、扩展信息，专门面向 Agent 工作流做上下文注入。
- Plan 能力从 PITR 扩展到更多高风险动作：新增 `pig ext add/rm --plan`、`pig pg stop/restart --plan`、`pig pt switchover/failover --plan`，并统一为可审阅执行计划（动作、影响面、风险、预期结果）。
- 结构化结果覆盖进一步完善：`pgbackrest info` 可嵌入原生 JSON 信息，Patroni/PostgreSQL/PITR/Repo/Ext 子系统的结构化返回与辅助 DTO 统一，兼容自动化消费。
- 兼容层增强：对 `pg_exporter/pg_probe/do/sty` 等存量命令引入 legacy structured wrapper，在保留旧交互行为的同时提供结构化执行结果与输出捕获。
- Pigsty 版本更新至 v4.1.0

## 扩展更新

| 扩展                 | 旧版本          | 新版本           |
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

## Bug 修复

- 安全修复：修复 `pig build proxy` 在异常地址输入下的解析 panic 问题。
- 安全修复：修复 `pig pg log` 文件名路径穿越风险，阻止通过 `../../` 访问日志目录外文件。
- 安全加固：加强 installer/repo 路径处理与引号处理，降低路径注入与异常路径误用风险。
- 构建链路可靠性修复：`pig build get/pkg/ext` 在下载或构建失败时正确传递错误并返回非零退出码；修复 DEB 构建中 `pg_ver` 不匹配导致的误报失败。
- 仓库与目录刷新修复：`ext/repo reload` 支持静默镜像回退；`repo add/set/rm` 在缓存更新失败时正确返回错误状态。
- 扩展管理修复：`ext update` 调整为显式目标更新并修复状态漂移问题；`ext import` 将请求的 DEB 资源下载到指定 repo 目录。
- 输出与可观察性修复：修复结构化输出 exit code 与文本渲染一致性问题；修复 `pg status` 权限处理与解析稳定性问题。

## 校验和

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

发布：https://github.com/pgsty/pig/releases/tag/v1.1.0
