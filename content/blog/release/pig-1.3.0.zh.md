---
title: "pig v1.3.0"
linkTitle: "v1.3.0"
date: 2026-02-27
author: "冯若航"
description: "构建链路强化，扩展增至 461，新内核支持"
categories: [release]
tags: [Release, pig]
weight: 120
---

这是从 `v1.2.0` 到 `v1.3.0` 的一次工程强化与目录扩展版本：15 commits、74 files changed、代码行 `+1184 / -236`。

该版本重点围绕 `pig build` 构建链路和 `ext` 目录/别名能力增强，并将可用扩展数量从 **451** 增加到 **461**。

## 主要变化

- 构建源码下载增强（`pig build get`）：
  - 支持从扩展 `Source` 字段解析多源码（空格/换行/Tab 分隔）并去重。
  - 新增 `agensgraph` / `agentsgraph` 源码映射。
  - `pgedge` 构建源码改为同时下载 `postgresql-17.9.tar.gz` 与 `spock-5.0.5.tar.gz`。
- 依赖解析与安装优化（`pig build dep`）：
  - RPM 依赖安装可从 spec 的 `pgmajorversion` 宏推断 PG 主版本，spec 缺失改为显式报错。
  - DEB 依赖解析支持 `Build-Depends` / `Build-Depends-Arch` / `Build-Depends-Indep` 的多行、候选依赖、架构限定与 profile 清理。
  - 支持 `PGVERSION` 占位符自动展开（优先 `--pg`，其次已安装版本与扩展元数据）。
  - 依赖安装失败降级为 warning，批量流程继续执行。
- DEB 构建结果判定修正（`pig build ext/pkg`）：
  - 构建命令退出码成功即判定成功，产物发现改为 best-effort 警告，避免误判失败。
  - 成功但无产物时不再显示空包列表横幅；部分产物场景标记 warning 而非 fail。
  - 构建日志中的源码与版本显示改为读取扩展元数据真实值，避免错误拼接 `name-version`。
- 扩展操作输出语义改进（`pig ext rm/update`）：
  - 别名解析后，`removed/updated` 返回值改为“实际包名”，方便自动化脚本精确比对。
- 扩展目录与别名更新：
  - 新增别名：`agensgraph` / `agens`、`pgedge`、`babelfishpg`。
  - `openhalodb` 对齐 PG14 包命名，`ivorysqldb` 命名对齐。
  - fork 元数据与可用性矩阵批量刷新（含 `timescaledb`、`pgmq`、`orioledb`、`documentdb`、`pg_tde`、`babelfishpg_*` 等条目）。
- 工程与发布：
  - 版本号提升到 `v1.3.0`（包含 `v1.2.1` 过渡提交），版权年份更新到 2026，README 同步更新到 461 扩展与最新 alias 说明。

## 兼容性提醒

- `pig ext rm/update` 结构化输出中的 `removed/updated` 字段由扩展名切换为包名；如果你的自动化逻辑按扩展别名匹配，请同步调整。

## 新增扩展（451 -> 461）

| 扩展名                  | 版本    | 说明                          |
|:---------------------|:------|:----------------------------|
| `aux_mysql`          | 1.5   | openHalo MySQL 兼容辅助模块（PG14） |
| `gb18030_2022`       | 1.0   | IvorySQL 编码转换模块             |
| `ivorysql_ora`       | 1.0   | IvorySQL Oracle 兼容扩展        |
| `ora_btree_gin`      | 1.0   | Oracle 类型 GIN 索引支持          |
| `ora_btree_gist`     | 1.0   | Oracle 类型 GiST 索引支持         |
| `pg_get_functiondef` | 1.0   | 获取函数定义                      |
| `plisql`             | 1.0   | PL/iSQL 过程语言                |
| `snowflake`          | 2.4   | pgEdge Snowflake ID 生成扩展    |
| `spock`              | 5.0.5 | pgEdge 多主逻辑复制扩展             |
| `lolor`              | 1.2.2 | pgEdge 大对象逻辑复制兼容扩展          |

## 完整提交列表（`v1.2.0..v1.3.0`）

- `b8ecf8d` 版本字符串更新到 1.2.1
- `55df9a4` `build/get` 支持多源码解析与 pgedge spock 源码
- `da8e347` 新增 agensgraph 和 pgedge 别名
- `86edbd7` `ext rm/update` 输出显示解析后的包名
- `ef3c905` `build/dep` 改进 rpm/deb 依赖解析
- `7144e09` 刷新 fork 元数据与可用性矩阵条目
- `befffbf` DEB 构建将成功命令视作权威结果
- `33fd517` DEB 成功但无产物时不再显示空包列表横幅
- `3b450f2` 下载源码时避免将扩展名与版本错误拼接
- `33847ab` `ext rm/update` 满足 staticcheck S1011
- `b8b917d` 依赖安装失败降级为 warning
- `8110c00` 调整 `ivorysqldb` / `babelfishpg` 别名
- `fac9faf` 版本提升到 1.3.0
- `1f88f06` 版权年份更新为 2026
- `c804757` `v1.3.0` 发布提交

## 校验和

```bash
196f32419886da095f303b1bcad2729b674abc03d412199e88a39390b2616534  pig-1.3.0-1.aarch64.rpm
a2dcc930dd47a08e85285c1fb7925e1355a1e67d458a265a7ef6d9666bc8e7ec  pig-1.3.0-1.x86_64.rpm
c7ebda6b9839408b12ffe1c8ea561f03e1793aae0732f9bbe2320a0d45160714  pig-v1.3.0.darwin-amd64.tar.gz
b717b485ed0a4a8c11dd8bf918400595b21df5ef43818836ec332f8518674c1a  pig-v1.3.0.darwin-arm64.tar.gz
40e6570c6ba0fe36c97950ff8de585eecb6bc1f862509a04f410a5f08ee90148  pig-v1.3.0.linux-amd64.tar.gz
d61430eeafc8005a22918a9aa60dea5c987916f9834331b5484f761b8235644f  pig-v1.3.0.linux-arm64.tar.gz
62c9a4fadc7dda393d6f28ab83b5f3d741e7d7f7de7abe40a5b89c393288519c  pig_1.3.0-1_amd64.deb
19261ae50e873a05a10a6ad500ab1b429b22e2612325c09f9cd5443dcd34308b  pig_1.3.0-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v1.3.0
