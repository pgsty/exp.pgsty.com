---
title: "复制采集器的身份、状态与权限修正"
linkTitle: "复制采集器修正"
date: "2026-10-22T00:00:00+08:00"
lastmod: "2026-10-23T00:00:00+08:00"
authors: [Vonng]
description: "订阅身份、接收器状态、复制源权限和关系计数的最小修正"
summary: "已随 v1.5.0 发布。给订阅增加数据库身份，修正接收器映射，明确可选权限与表、序列的计数口径。"
categories: [design]
tags: [Design, PostgreSQL, Compatibility, Prometheus]
---

> **状态：** 已随 v1.5.0 发布。<br>
> **决策日期 / 最近核验：** 2026-10-22 / 2026-10-23。<br>
> **范围：** pg_exporter `main` 提交 `d97ba38fc8390984df994b2f9ea58b43ecfc8b89` 中的 Collector 修正，基于 `72f00a4fa4e6eb7524174f2122b3fe1e1d608db4`；PostgreSQL `REL_19_RC1` 对应 `0b8bff042a997fe50fcd1c4c83b9ef1cc9ed8a89`，另作 PG9.6–18 的针对性检查。这些修正从 v1.5.0 开始发布，v1.4.1 不包含。<br>
> **交付：** 源码已提交并推送，v1.5.0 标签指向 `18912540fe5edce0ed0ee81fac0d989738ecaa87`；CI 与正式发布工作流通过，GitHub Release、RPM／DEB／压缩包和 Docker 镜像已发布。未据此声称生产部署或生产负载验收完成。

## 已选定的修正 {#decisions}

| 问题 | 决策 | 保留行为 |
|:---|:---|:---|
| 不同数据库的同名订阅产生重复指标样本 | 给全部 `pg_sub` 版本分支添加 `datname` | 原指标族，包括 `pg_sub_id`；cluster 范围、worker 过滤和数值 |
| Receiver CASE 混入 sender 状态名称 | 补足真实 receiver 字典并修正 HELP | 已有效的 0、4、5 编码；未知与 NULL 仍为 -1 |
| 可选 origin 采集器的权限说明不完整 | 保持 `skip: true`，说明用户自行授权及版本限制 | 原 SQL、指标和默认关闭行为 |
| 发布与订阅的关系数量统计集合不同 | 校正 HELP 与手册 | SQL、标签、数值和缺失样本行为；不新增序列指标 |
{.wide .expand}

## 订阅身份 {#subscription-identity}

`(datname, subname)` 可以唯一标识同一 PostgreSQL 集群中的订阅。上游对 `(subdbid, subname)` 有唯一约束，数据库名在同一集群内也唯一。查询必须通过订阅 OID 找到真实归属数据库：

```sql
JOIN pg_catalog.pg_subscription s ON s.oid = subscription_id
JOIN pg_catalog.pg_database d ON d.oid = s.subdbid
```

这里的 `subscription_id` 指现有来源别名：PG19 分支用 `s2.subid`，更早分支用统计视图中的 subid。把 `d.datname` 加入结果并声明为 LABEL。不能使用 `CURRENT_DATABASE()`，不能仅按订阅名关联，也不能把连接库名作为常量标签代替实际归属。

查询仍必须保持每个订阅一行。保留 apply leader 过滤和 PG19 对 sequence synchronization worker 的排除。数据库身份区分不同订阅；worker 过滤避免同一订阅重复出行，两者分别必要。

### PG10–13 的额外权限前提 {#postgresql-10-13-permission-prerequisite}

PG10–13 遗漏了 `pg_subscription.oid` 的默认公开读取权限。上游明确只为 PG14 修正，没有修改旧分支。因此，数据库标签方案在这些旧版本上有一项升级前提：

```sql
-- 由管理员在 exporter 主连接所使用的数据库中执行。
GRANT SELECT (oid) ON pg_catalog.pg_subscription TO monitor;
```

应替换为实际监控角色。授权应在每个可能作为 exporter 主连接的数据库中执行，不能只在订阅所在库执行；它不会授予 `subconninfo` 权限。PG14+ 在标准目录 ACL 下无需为此关联增加授权；用户自行收紧的 ACL 仍由用户管理。

这是一项部署成本，不是自动权限修复。PG10–13 必须先授权，再部署修改后的配置。缺权限时查询失败，订阅指标缺失，但 HTTP 仍可能是 200；因此验收必须同时检查预期样本与查询错误，不能只检查 HTTP 状态。

### 替代方案与迁移代价 {#alternatives-and-migration}

额外增加 `subid` 标签可以省掉两个关联及旧版本授权。此次选定数据库身份，是为了便于按数据库阅读、筛选，并与其他 Collector 的标签习惯一致。在此需求下，两个目录关联和一项明确的旧版列授权，比新建权限包装函数或运行时 fallback 更小。不同时添加两种身份标签。

保留 `id` GAUGE，不把它改成 LABEL 而删除 `pg_sub_id`。指标族名称与样本数量保持不变，但新标签会产生新时序；应检查对标签敏感的 PromQL 联接与聚合。数据库或订阅改名也会改变身份。跨集群仍由目标标签区分。

## Receiver 状态字典 {#receiver-state-dictionary}

已逐个对照 PG9.6 至 PG19 RC1 的发布边界源码。PG9.6–18 有六个 receiver 状态，PG19 增加 `connecting`。

| Receiver 字符串 | 编码 | 适用范围 |
|:---|---:|:---|
| streaming | 0 | PG9.6–19 |
| stopping | 4 | PG9.6–19 |
| connecting | 5 | PG19；旧服务器不会产生此值 |
| starting | 6 | PG9.6–19 |
| waiting | 7 | PG9.6–19 |
| restarting | 8 | PG9.6–19 |
| stopped | 9 | PG9.6–19 |
| 其他或 NULL | -1 | 全部分支 |

从 receiver CASE 与 HELP 中移除 `startup`、`catchup`、`backup`。旧编码 1–3 留空，不重新赋义。对当前三个分支及 legacy 的 `pg_recv_96` 使用一致字典，无需新版本分支或 Go 状态逻辑。

内部枚举存在不代表统计视图一定有可见行。RC1 在 PID 为零或统计未准备好时不返回 receiver 行；无行时不能制造 stopped 或 streaming 样本。保留连接中 sender host / port 为 NULL 的处理。

对抗性测试还发现，legacy receiver 查询在 PG9.6 上调用了 PG10 才引入的 `regexp_match()`。将两处取首个捕获组的表达式改为标量 `substring(... FROM ...)`，即可让查询在 PG9.6 执行，不增加版本分支、集合返回函数或 conninfo 解析器。正则表达式与得到的 host / port 标签保持一致。这一直接前提随字典修正一起处理。

PG9.6 自身只向非超级用户展示 receiver PID，其余统计字段为 NULL，因此该角色下状态为 -1。修复 SQL 兼容性不会绕过这种可见性规则，也不意味着应向监控账号授予超级用户权限。

最终 legacy 查询已在 PG9.6–12 执行。真实 PG9.6.24 备库向管理员返回 streaming 状态 0，向普通 monitor 返回状态 -1；该监控角色的 HTTP 抓取返回 200 与 11 个 receiver 样本。host / port fixture 覆盖缺失字段、NULL、Unix 路径、IPv6、重复键与带引号输入；PG10–12 的新旧提取表达式结果一致。这里保留原有正则语义，包括其对含空格引号值的既有限制。

## 可选复制源采集 {#optional-replication-origins}

当前与 legacy 配置已经设置 `skip: true`，应原样保留。文档明确由用户先准备权限，再显式启用。

采用标准目录 ACL 的 PG14+ 可由管理员给实际监控角色授权：

```sql
GRANT SELECT ON pg_catalog.pg_replication_origin_status TO monitor;
GRANT EXECUTE ON FUNCTION
  pg_catalog.pg_show_replication_origin_status() TO monitor;
```

授权在 exporter 主连接使用的数据库中执行。PG13 及以前保留函数内部的超级用户检查，仅 GRANT 不能让普通监控角色直接使用；除非管理员另行选择并维护访问方案，否则保持可选入口关闭。本次不添加 SECURITY DEFINER 包装函数、自动 GRANT、切换身份重试或伪造零值。

标准 ACL 已允许公开读取 `pg_replication_origin` 目录，因此不需要重复授权。若部署收紧过目录 ACL，管理员还需自行准备查询所需的目录读取权限。

## 发布与订阅计数 {#publication-and-subscription-counts}

文档描述当前真实行为：

- `pg_pubrel_count` 统计 `pg_get_publication_tables()` 返回的表，不包括序列。现有 CROSS LATERAL 查询对空发布、纯序列发布不输出行；缺失不是显式的零。
- PG19 的 `pg_subrel_count` 按同步状态统计 `pg_subscription_rel` 中的表与序列。PG19 表状态为 i/d/f/s/r，序列状态为 i/r。
- 两端计数不构成复制健康的等式。多 publication、对象重叠、分区、refresh 和异步同步都会影响解释。

只修改说明与手册。保留订阅关系查询的 `DISTINCT subid, subname`，不在此补丁增加 `pg_pubseq_count`、`relkind` 标签、补零或新的对象计数定义。

## 验证证据与剩余关口 {#validation-and-remaining-gates}

最终配置和从上述 `main` 基线构建的二进制，已由非超级用户监控角色在 PG10.21、11.16、12.22、13.23、14.23、15.18、16.14、17.10、18.4 和 19 RC1 上验证。两个数据库中的同名订阅得到不同标签，重复样本键为零。PG10–13 在列授权前失败，仅在订阅库授权后仍失败，在主连接库授权后通过；始终不能读取 `subconninfo`。PG10–14 分支输出 14 个样本，PG15–18 输出 18 个，PG19 输出 42 个，差异来自原有指标族数量。

RC1 完整配置验证覆盖 disabled、active、自动发现开关及物理备库。针对性 HTTP 验证在抓取前后均捕获 table-sync / sequence-sync 与 apply worker 并存，订阅样本仍为 42 个。完整默认计划未选择 `pg_origin`。Receiver 枚举 fixture 覆盖 PG9.6 和 PG10–19 各大版本；另实际观察 RC1 streaming 与 connecting，后者 sender 字段为 NULL 时 HTTP 仍正确输出状态 5。枚举 fixture 不等于实际观察过所有瞬态。

使用真实 origin 条目的测试确认：仅授权视图不足；PG14+ 补充文档中的函数授权后成功，PG13 及更早版本仍拒绝非超级用户。空 origin 目录不足以证明权限正确，因为 LEFT JOIN 可能不调用受限函数。RC1 中，混合发布输出一个表，订阅端统计一个表加一个序列；空发布和纯序列发布不输出行。

本地 Go race 测试、兼容 HTTP-mux 模式、`go vet`、依赖一致性，以及已有的 schema、版本覆盖、生成文件一致性、常量标签冲突检查均通过。无需修改 Go 实现或依赖。源码验证与双语文档构建独立于发布和生产验收。

## 实施边界 {#implementation-boundaries}

源码范围限于七个拆分 Collector 文件及两个生成配置包；companion 范围为成对的 Collector 手册和本 Design 记录。手册区分已有权限 / 计数语义与 v1.5.0 的身份、状态字典、PG9.6 SQL 修正。源码审阅、提交、推送、标签与正式制品发布均已完成；生产部署仍是独立动作。

不包含驱动迁移、Gatherer 重构、运行时权限管理、新 Collector 分支、新指标族、订阅关系聚合改写或无关 legacy SQL 修复。

## 上游依据 {#primary-references}

- [RC1 订阅身份约束](https://github.com/postgres/postgres/blob/0b8bff042a997fe50fcd1c4c83b9ef1cc9ed8a89/src/include/catalog/pg_subscription.h)
- [PG14 对订阅列权限的修正](https://github.com/postgres/postgres/commit/3590680b85a8e51ef8df550e5a10dedd0d2dfd88)
- [RC1 receiver 状态与可见性实现](https://github.com/postgres/postgres/blob/0b8bff042a997fe50fcd1c4c83b9ef1cc9ed8a89/src/backend/replication/walreceiver.c)
- [PG14 origin 函数权限调整](https://github.com/postgres/postgres/commit/cc072641d41c55c6aa24a331fc1f8029e0a8d799)
- [RC1 系统视图](https://github.com/postgres/postgres/blob/0b8bff042a997fe50fcd1c4c83b9ef1cc9ed8a89/src/backend/catalog/system_views.sql)
