---
title: "内置采集器"
linkTitle: "采集器"
description: "PG Exporter 内置 58 个采集器定义文件的完整清单、前置条件与运维建议"
weight: 100
icon: fa-solid fa-table-list
categories: [参考]
---

PG Exporter v{{< param version >}} 在 [`config/`](https://github.com/pgsty/pg_exporter/tree/v1.6.1/config) 中提供 **58 个 YAML 文件**（57 个采集器文件和 1 个配置参考文件），`make conf` 按文件名顺序将它们合并为默认的 [`pg_exporter.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/pg_exporter.yml)。

文件名前缀只负责排序，并不是指标名。一个文件可以为同一指标命名空间定义多个版本或角色分支。PG Exporter 在首次抓取时根据目标实例信息选择符合条件的分支；对真实目标访问 [`GET /explain`](/zh/api/#get-explain)，即可查看最终执行计划。

按指标名称跨版本分支去重，v1.6.1 定义了 **59 个采集器命名空间、460 个指标名**，其中包含默认禁用的采集器和 2 个 `HISTOGRAM` 定义，尚未展开直方图。一次抓取的实际序列数取决于选中的分支、结果行、标签和桶数。

升级 PostgreSQL 或替换采集器配置前，请核对[指标兼容性与迁移对照表](/zh/compatibility/#metric-compatibility)。其中区分 v1.5.0 的标签／状态修正、PG19 的新增指标与语义变化、较早 PostgreSQL 版本已移除的指标，并提供避免告警因时序缺失而静默的检查方法。

## 编号分区 {#numbering-map}

| 范围 | 领域 | 典型范围 |
|:---|:---|:---|
| `0000` | 编写参考 | YAML 模式与示例，不包含可执行采集器 |
| `0100` | 身份与设置 | 实例身份、元数据、配置容量上限 |
| `0200` | 复制 | 发送端、接收端、复制槽、订阅、复制源 |
| `0300` | 实例内部 | I/O、存储、检查点、恢复、SLRU、共享内存 |
| `0400` | 工作负载 | WAL、会话、等待、事务、锁、查询统计 |
| `0500` | 进度 | VACUUM、建索引、聚簇、基础备份进度 |
| `0600` | 数据库与逻辑复制 | 数据库计数、冲突、发布与订阅状态 |
| `0700` | 关系对象 | 表、索引、函数、序列、分区 |
| `0800` | 高开销关系分析 | 对象大小与膨胀 |
| `0900` | PgBouncer | 列表、数据库、统计、连接池 |
| `1000+` | 可选集成 | 等待采样、TimescaleDB、Citus、心跳 |
{.full-width .wide .expand}

## 完整清单 {#complete-inventory}

| 文件 | 命名空间 | 范围与前置条件 |
|:---|:---|:---|
| [`0000-doc.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0000-doc.yml) | 配置参考 | YAML 模式与采集器编写指南，不包含可执行采集器 |
| [`0110-pg.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0110-pg.yml) | `pg` | 实例基础信息，区分主库与从库分支 |
| [`0120-pg_meta.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0120-pg_meta.yml) | `pg_meta` | 集群元数据；PG13+ 包含 `primary_conninfo` |
| [`0130-pg_setting.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0130-pg_setting.yml) | `pg_setting` | 共享参数与容量上限 |
| [`0210-pg_repl.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0210-pg_repl.yml) | `pg_repl` | 复制发送端统计 |
| [`0220-pg_sync_standby.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0220-pg_sync_standby.yml) | `pg_sync_standby` | 同步备库状态 |
| [`0230-pg_downstream.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0230-pg_downstream.yml) | `pg_downstream` | 下游复制客户端数量 |
| [`0240-pg_slot.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0240-pg_slot.yml) | `pg_slot` | 复制槽；PG16+ 支持备库，PG19 支持新的失效原因 |
| [`0250-pg_recv.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0250-pg_recv.yml) | `pg_recv` | 备库 WAL 接收器；支持 PG19 `connecting` 状态 |
| [`0260-pg_sub.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0260-pg_sub.yml) | `pg_sub` | 订阅统计；PG19 同步错误与冲突计数 |
| [`0270-pg_origin.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0270-pg_origin.yml) | `pg_origin` | 复制源状态；默认禁用，可能需要额外权限 |
| [`0300-pg_io.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0300-pg_io.yml) | `pg_io` | PG16+ 的 `pg_stat_io`，含 PG18+ 分支 |
| [`0310-pg_size.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0310-pg_size.yml) | `pg_size` | 数据库、WAL 与日志大小 |
| [`0320-pg_archiver.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0320-pg_archiver.yml) | `pg_archiver` | 归档进程统计 |
| [`0330-pg_bgwriter.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0330-pg_bgwriter.yml) | `pg_bgwriter` | 后台写进程统计，包含 PG17+ 分支 |
| [`0331-pg_checkpointer.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0331-pg_checkpointer.yml) | `pg_checkpointer` | 检查点进程统计；PG18+ 完成量与 SLRU 计数 |
| [`0340-pg_ssl.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0340-pg_ssl.yml) | `pg_ssl` | SSL 客户端连接数量 |
| [`0350-pg_checkpoint.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0350-pg_checkpoint.yml) | `pg_checkpoint` | 检查点控制信息 |
| [`0355-pg_timeline.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0355-pg_timeline.yml) | `pg_timeline` | 主库或备库的当前时间线 ID |
| [`0360-pg_recovery.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0360-pg_recovery.yml) | `pg_recovery`, `pg_recovery_prefetch` | 备库恢复与恢复预取统计 |
| [`0370-pg_recovery_state.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0370-pg_recovery_state.yml) | `pg_recovery_state` | PG19 备库 `pg_stat_recovery` 恢复状态 |
| [`0380-pg_slru.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0380-pg_slru.yml) | `pg_slru` | PG13+ SLRU 缓存统计 |
| [`0390-pg_shmem.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0390-pg_shmem.yml) | `pg_shmem` | 共享内存分配；默认禁用，要求 `schema:monitor` |
| [`0400-pg_wal.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0400-pg_wal.yml) | `pg_wal` | PG14+ WAL 统计；PG19 增加全页写字节计数 |
| [`0410-pg_activity.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0410-pg_activity.yml) | `pg_activity` | 按数据库与状态统计后端连接 |
| [`0420-pg_wait.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0420-pg_wait.yml) | `pg_wait` | 按等待事件类型统计后端等待 |
| [`0430-pg_backend.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0430-pg_backend.yml) | `pg_backend` | 按 `backend_type` 汇总后端进程 |
| [`0440-pg_xact.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0440-pg_xact.yml) | `pg_xact` | 事务快照边界与活跃事务数量 |
| [`0450-pg_xact_age.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0450-pg_xact_age.yml) | `pg_xact_age` | PG10+ 各数据库未结束事务与事务内空闲的年龄快照直方图 |
| [`0460-pg_lock.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0460-pg_lock.yml) | `pg_lock` | 按数据库与模式统计锁分布 |
| [`0470-pg_lock_stat.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0470-pg_lock_stat.yml) | `pg_lock_stat` | PG19 全局锁等待与快速路径溢出计数 |
| [`0480-pg_query.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0480-pg_query.yml) | `pg_query` | 查询统计；要求 `extension:pg_stat_statements` |
| [`0510-pg_vacuuming.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0510-pg_vacuuming.yml) | `pg_vacuuming` | 仅主库的 VACUUM 进度；PG18+ 包含 `delay_time` |
| [`0520-pg_indexing.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0520-pg_indexing.yml) | `pg_indexing` | 仅主库的 `CREATE INDEX` 进度 |
| [`0530-pg_clustering.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0530-pg_clustering.yml) | `pg_clustering` | 仅主库的 `CLUSTER` 与 `VACUUM FULL` 进度 |
| [`0540-pg_backup.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0540-pg_backup.yml) | `pg_backup` | PG13+ 基础备份进度 |
| [`0610-pg_db.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0610-pg_db.yml) | `pg_db` | 各数据库统计；PG18+ 并行工作进程计数 |
| [`0620-pg_db_confl.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0620-pg_db_confl.yml) | `pg_db_confl` | 备库数据库冲突计数 |
| [`0640-pg_pubrel.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0640-pg_pubrel.yml) | `pg_pubrel` | 发布与发布关系数量 |
| [`0650-pg_subrel.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0650-pg_subrel.yml) | `pg_subrel` | 按状态汇总订阅关系 |
| [`0660-pg_vacuum_score.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0660-pg_vacuum_score.yml) | `pg_vacuum_score` | PG19 主库 `pg_stat_autovacuum_scores` 自动清理评分摘要 |
| [`0700-pg_table.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0700-pg_table.yml) | `pg_table` | 每表统计；PG18+ 维护时间与新页面更新计数 |
| [`0710-pg_index.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0710-pg_index.yml) | `pg_index` | 每索引统计 |
| [`0720-pg_func.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0720-pg_func.yml) | `pg_func` | 函数执行统计 |
| [`0730-pg_seq.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0730-pg_seq.yml) | `pg_seq` | 序列指标 |
| [`0740-pg_relkind.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0740-pg_relkind.yml) | `pg_relkind` | 按关系类型统计对象数量 |
| [`0750-pg_defpart.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0750-pg_defpart.yml) | `pg_defpart` | 默认分区元组数量 |
| [`0810-pg_table_size.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0810-pg_table_size.yml) | `pg_table_size` | 每表大小；在超大模式中可能较慢 |
| [`0820-pg_table_bloat.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0820-pg_table_bloat.yml) | `pg_table_bloat` | 默认禁用；要求辅助视图 `pg_table_bloat` |
| [`0830-pg_index_bloat.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0830-pg_index_bloat.yml) | `pg_index_bloat` | 默认禁用；要求辅助视图 `pg_index_bloat` |
| [`0910-pgbouncer_list.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0910-pgbouncer_list.yml) | `pgbouncer_list` | 从管理数据库获取 PgBouncer 列表指标 |
| [`0920-pgbouncer_database.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0920-pgbouncer_database.yml) | `pgbouncer_database` | PgBouncer 数据库指标，含版本分支 |
| [`0930-pgbouncer_stat.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0930-pgbouncer_stat.yml) | `pgbouncer_stat` | PgBouncer 各数据库统计，含版本分支 |
| [`0940-pgbouncer_pool.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/0940-pgbouncer_pool.yml) | `pgbouncer_pool` | PgBouncer 连接池指标，含版本分支 |
| [`1000-pg_wait_event.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/1000-pg_wait_event.yml) | `pg_wait_event`, `pg_wait_event_1s` | 等待事件采样；要求 `extension:pg_wait_sampling` |
| [`1800-pg_tsdb_hypertable.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/1800-pg_tsdb_hypertable.yml) | `pg_tsdb_hypertable` | 默认禁用；要求 TimescaleDB 及其信息模式 |
| [`1900-pg_citus.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/1900-pg_citus.yml) | `pg_citus_node` | Citus 工作节点/协调节点清单；要求 `extension:citus` |
| [`2000-pg_heartbeat.yml`](https://github.com/pgsty/pg_exporter/blob/v1.6.1/config/2000-pg_heartbeat.yml) | `pg_heartbeat` | 默认禁用；要求 `postgres` 库中的 `monitor.heartbeat` 表 |
{.full-width .wide .expand}

> [!NOTE]
> **自 v1.6.0 起：** VACUUM、建索引与 CLUSTER 进度保持集群级采集；`relname` 在当前连接库及系统目录上解析名称，其他库的关系使用数字 OID，自动发现过滤不影响此覆盖。现有安装需更新采集器 YAML。详见[进度指标的数据库范围](/zh/design/progress-database-scope/)。

## 启用前先看计划 {#plan-before-enabling}

规划器根据目标类型、服务器版本、恢复角色、数据库、扩展、模式、用户名和标签筛选分支。谓词查询在之后刷新采集结果时执行。先完成一次抓取，再查看主连接的当前计划：

```bash
curl -fsS http://127.0.0.1:9630/metrics >/dev/null
curl -fsS http://127.0.0.1:9630/explain
```

`/explain` 返回选中的采集器的纯文本说明。用 `--log.level=debug` 查看分支被排除的原因。

`pg_origin`、`pg_shmem`、两个膨胀采集器、TimescaleDB 采集器和 `pg_heartbeat` 均设置了 `skip: true`。准备好所需权限和对象后，再改为 `skip: false`。心跳采集器只负责读取，心跳表由独立任务维护。

### 复制源权限 {#replication-origin-permissions}

`pg_origin` 保持默认关闭。在采用标准目录 ACL 的 PostgreSQL 14+ 上，由管理员在 Exporter 的 **主连接数据库** 中执行以下授权，将 `monitor` 替换为实际监控角色：

```sql
GRANT SELECT ON pg_catalog.pg_replication_origin_status TO monitor;
GRANT EXECUTE ON FUNCTION
  pg_catalog.pg_show_replication_origin_status() TO monitor;
```

之后在实际加载的配置中显式将此采集器设为 `skip: false`，重载或重启 Exporter，并核对查询错误和预期的 origin 指标。只有 `pg_monitor` 成员身份并不足够。PostgreSQL 13 及更早版本还会在函数内部检查超级用户身份，上述授权无法让普通监控角色直接调用，应保持此可选采集器关闭。Exporter 不会自动授予权限。

### 发布与订阅计数 {#publication-and-subscription-counts}

`pg_pubrel_count` 统计 `pg_get_publication_tables()` 返回的表条目，即使在 PG19 上也不包含序列。空发布和仅包含序列的发布 **不会产生时序**，而不是显式输出零。

`pg_subrel_count` 按订阅和同步状态汇总 `pg_subscription_rel` 中的条目。PG19 上包含表和序列。表状态为 `i`（初始化）、`d`（复制数据）、`f`（表数据复制完成）、`s`（已同步）和 `r`（就绪）；PG19 序列使用 `i` 或 `r`。

不能用发布端与订阅端数量相等来判断复制健康：两者统计的集合不同，发布重叠、分区处理、刷新与同步进度也会影响数量。

### 订阅身份与接收器状态 {#subscription-identity-and-receiver-states}

v1.5.0 配置修正了订阅身份与接收器状态。替换旧采集器配置时，请核对以下升级要求：

- 全部 `pg_sub_*` 样本增加表示订阅归属数据库的 `datname` 标签，与 `subname` 一起区分跨库同名订阅。保留原有 `pg_sub_id` gauge。新增标签会产生新时序，部署前应检查依赖标签匹配的 PromQL 连接与聚合。
- PG10–13 部署新配置前，管理员须在每个用作 Exporter **主连接数据库** 的库内执行 `GRANT SELECT (oid) ON pg_catalog.pg_subscription TO monitor;`。仅在订阅所在数据库授权并不足够。该授权不会开放 `subconninfo`。PG14+ 在标准目录 ACL 下不需要额外授权。缺少此前提时，订阅查询会失败且指标缺失；HTTP 200 不能单独证明抓取成功。
- 当前与 legacy 配置的 `pg_recv_state` 均使用下表。编码 1–3 保留；PG9.6–18 不存在 `connecting` 状态。没有 receiver 行时仍不输出样本，不填零，也不伪造 stopped 状态。
- Legacy receiver 查询使用 PG9.6 兼容的标量 `substring()` 提取 host 和 port。PG9.6 仍会对非超级用户隐藏 receiver 详情：只有 PID 可见，采集器输出状态 -1。这项 SQL 修正不改变数据库权限。

| 状态 | 编码 | 状态 | 编码 |
|:---|---:|:---|---:|
| streaming | 0 | starting | 6 |
| stopping | 4 | waiting | 7 |
| connecting（PG19+） | 5 | restarting | 8 |
| 未知 / NULL | -1 | stopped | 9 |

## 基数与开销 {#cardinality-and-cost}

每对象和每查询采集器是主要的基数来源。在大规模环境中启用前重点检查：

- `pg_table`、`pg_index`、`pg_func`、`pg_seq` 会为每个对象产生一组或多组时序。
- `pg_query` 从 `pg_stat_statements` 中按调用次数选择最多 128 组语句。查询 ID 会随时间变化。
- `pg_table_size`、`pg_table_bloat`、`pg_index_bloat` 在关系很多时可能成本较高。
- 等待事件采样依赖扩展，并可能产生随负载变化的维度。

用 `ttl` 控制高开销 SQL 的执行频率，按实测耗时设置 `timeout`。抓取超时需要容纳所有采集器和自动发现数据库的完整采集过程。变更前后比较 `pg_exporter_scrape_duration` 和时序数量。

## 定制采集器 {#customize-collectors}

先复制完整的配置目录，再将本地定义放入排序靠后的文件，如 `9990-local.yml`。覆盖已有分支时，使用相同的顶层键并提供完整定义；目录加载会替换整个分支。新分支使用唯一键，同一指标族的版本范围应互不重叠。

显式选择该目录并验证：

```bash
pg_exporter --config=/path/to/collectors --dry-run
# 在一个终端中运行服务
PG_EXPORTER_CONFIG=/path/to/collectors pg_exporter

# 在另一个终端中先抓取，再查看计划
curl -fsS http://127.0.0.1:9630/metrics >/dev/null
curl -fsS http://127.0.0.1:9630/explain
```

采集器模式、查询到指标的映射、标签、谓词、缓存、超时与直方图规则详见[采集器配置](/zh/config/)。
