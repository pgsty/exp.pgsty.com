---
title: "pig v1.2.0"
linkTitle: "v1.2.0"
date: 2026-02-23
author: "冯若航"
description: "统一别名，例行更新，计划模式，仓库修复"
categories: [release]
tags: [Release, pig]
weight: 130
---

- 扩展目录与别名解析增强：
  - 引入动态 PG 分类别名解析，按 PG 主版本选择别名映射。
  - 引入 OS 维度别名覆盖（ansible/bootstrap），并在未知发行版回退中收敛为 PGDG-only。
  - 新增 `node/infra`、`babelfish/cloudberry` 等别名并更新扩展元数据，减少包解析歧义。
- 高风险操作计划预览：
  - 新增 `pig install --plan`，支持结构化执行计划输出。
  - 统一 `pig pitr` 与 pgBackRest `repack/expire` 的计划预览语义。
  - 新增 plan flag 一致性测试，确保子命令行为对齐。
- `sty` 原生配置能力：
  - 新增 `pig sty configure` 命令及完整执行流（preflight、参数处理、执行编排）。
  - 统一 `sty conf/configure` 行为，默认走原生实现并保留 `--raw` 回退。
  - 补充 configure 主流程、preflight、路由与安装联动测试，提升可维护性。
- 仓库/构建/可靠性修复：
  - 修复 repo cache 在 `os.Stat` 错误场景中的 nil dereference。
  - 对齐 Ubuntu 与 Debian 仓库 channel 映射，补充 reload 镜像拉取超时控制。
  - 加固 `repo rm` 对 dotted module 名称的安全删除与路径校验。
  - 修复 `sty init` 与 build 相关符号链接保留、跨设备迁移与目标目录处理问题。
  - 改进文本输出与矩阵配色渲染，修复 ext 命令空参数与空目标校验问题。

- 35 Commit，66 文件变更，代码行：`+5006 / -379`

- **PG 扩展与内核包更新**

| 包名                  | 旧版本      | 新版本      | 备注                    |
|:--------------------|:---------|:---------|:----------------------|
| `timescaledb`       | 2.25.0   | 2.25.1   |                       |
| `citus`             | 14.0.0-3 | 14.0.0-4 | 使用最新官方版本重新构建          |
| `age`               | 1.7.0    | 1.7.0    | 新增 PG 17 的 1.7.0 版本支持 |
| `pg_background`     | -        | 1.8      | 仅构建 DEB 包，RPM 来自 PGDG |
| `pgmq`              | 1.10.0   | 1.10.1   | 当前没有该扩展包              |
| `pg_search`         | 0.21.6   | 0.21.8   | 直接下载使用                |
| `oriolepg`          | 17.11    | 17.16    | OriolePG 内核更新         |
| `orioledb`          | beta12   | beta14   | 配套 OriolePG 17.16     |
| `cloudberry`        | -        | 2.0.0    | 新增包                   |
| `babelfishpg`       | -        | 5.5.0    | 新增 BabelfishPG 包组     |
| `babelfish`         | -        | 5.5.0    | 新增 Babelfish 兼容包      |
| `antlr4-runtime413` | -        | 4.13     | 新增 Babelfish 依赖运行时    |


## 校验和

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

发布：https://github.com/pgsty/pig/releases/tag/v1.2.0
