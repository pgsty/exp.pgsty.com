---
title: "内置采集器"
linkTitle: "采集器"
description: "PG Exporter 内置 58 个采集器定义文件的完整清单、前置条件与运维建议"
weight: 100
icon: fa-solid fa-table-list
categories: [参考]
---

PG Exporter v{{< param version >}} 在 [`config/`](https://github.com/pgsty/pg_exporter/tree/main/config) 中提供 **58 个采集器定义文件**，`make conf` 按文件名顺序将它们合并为默认的 [`pg_exporter.yml`](https://github.com/pgsty/pg_exporter/blob/main/pg_exporter.yml)。

文件名前缀只负责排序，并不是指标名。一个文件可以为同一指标命名空间定义多个版本或角色分支。PG Exporter 启动时根据目标实例事实只安装符合条件的分支；对真实目标访问 [`GET /explain`](/zh/api/#get-explain)，即可查看最终执行计划。

## 编号分区

| 范围 | 领域 | 典型范围 |
|:---|:---|:---|
| `0000` | 编写参考 | YAML 模式与示例，不会安装为采集器 |
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
{.full-width}

## 完整清单

| 文件 | 命名空间 | 范围与前置条件 |
|:---|:---|:---|
| [`0000-doc.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0000-doc.yml) | 配置参考 | YAML 模式与采集器编写指南，不会被安装 |
| [`0110-pg.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0110-pg.yml) | `pg` | 实例基础信息，区分主库与从库分支 |
| [`0120-pg_meta.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0120-pg_meta.yml) | `pg_meta` | 集群元数据；PG13+ 包含 `primary_conninfo` |
| [`0130-pg_setting.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0130-pg_setting.yml) | `pg_setting` | 共享参数与容量上限 |
| [`0210-pg_repl.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0210-pg_repl.yml) | `pg_repl` | 复制发送端统计 |
| [`0220-pg_sync_standby.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0220-pg_sync_standby.yml) | `pg_sync_standby` | 同步备库状态 |
| [`0230-pg_downstream.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0230-pg_downstream.yml) | `pg_downstream` | 下游复制客户端数量 |
| [`0240-pg_slot.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0240-pg_slot.yml) | `pg_slot` | 复制槽；PG16+ 支持备库，PG19 支持新的失效原因 |
| [`0250-pg_recv.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0250-pg_recv.yml) | `pg_recv` | 备库 WAL 接收器；支持 PG19 `connecting` 状态 |
| [`0260-pg_sub.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0260-pg_sub.yml) | `pg_sub` | 订阅统计；PG19 同步错误与冲突计数 |
| [`0270-pg_origin.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0270-pg_origin.yml) | `pg_origin` | 复制源状态；默认禁用，可能需要额外权限 |
| [`0300-pg_io.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0300-pg_io.yml) | `pg_io` | PG16+ 的 `pg_stat_io`，含 PG18+ 分支 |
| [`0310-pg_size.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0310-pg_size.yml) | `pg_size` | 数据库、WAL 与日志大小 |
| [`0320-pg_archiver.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0320-pg_archiver.yml) | `pg_archiver` | 归档进程统计 |
| [`0330-pg_bgwriter.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0330-pg_bgwriter.yml) | `pg_bgwriter` | 后台写进程统计，包含 PG17+ 分支 |
| [`0331-pg_checkpointer.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0331-pg_checkpointer.yml) | `pg_checkpointer` | 检查点进程统计；PG18+ 完成量与 SLRU 计数 |
| [`0340-pg_ssl.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0340-pg_ssl.yml) | `pg_ssl` | SSL 客户端连接数量 |
| [`0350-pg_checkpoint.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0350-pg_checkpoint.yml) | `pg_checkpoint` | 检查点控制信息 |
| [`0355-pg_timeline.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0355-pg_timeline.yml) | `pg_timeline` | 主库或备库的当前时间线 ID |
| [`0360-pg_recovery.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0360-pg_recovery.yml) | `pg_recovery`, `pg_recovery_prefetch` | 备库恢复与恢复预取统计 |
| [`0370-pg_recovery_state.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0370-pg_recovery_state.yml) | `pg_recovery_state` | PG19 备库 `pg_stat_recovery` 恢复状态 |
| [`0380-pg_slru.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0380-pg_slru.yml) | `pg_slru` | PG13+ SLRU 缓存统计 |
| [`0390-pg_shmem.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0390-pg_shmem.yml) | `pg_shmem` | 共享内存分配；默认禁用，要求 `schema:monitor` |
| [`0400-pg_wal.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0400-pg_wal.yml) | `pg_wal` | PG14+ WAL 统计；PG19 增加全页写字节计数 |
| [`0410-pg_activity.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0410-pg_activity.yml) | `pg_activity` | 按数据库与状态统计后端连接 |
| [`0420-pg_wait.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0420-pg_wait.yml) | `pg_wait` | 按等待事件类型统计后端等待 |
| [`0430-pg_backend.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0430-pg_backend.yml) | `pg_backend` | 按 `backend_type` 汇总后端进程 |
| [`0440-pg_xact.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0440-pg_xact.yml) | `pg_xact` | 事务快照边界与活跃事务数量 |
| [`0450-pg_xact_age.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0450-pg_xact_age.yml) | `pg_xact_age` | PG10+ 各数据库活跃/空闲事务年龄直方图 |
| [`0460-pg_lock.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0460-pg_lock.yml) | `pg_lock` | 按数据库与模式统计锁分布 |
| [`0470-pg_lock_stat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0470-pg_lock_stat.yml) | `pg_lock_stat` | PG19 全局锁等待与快速路径溢出计数 |
| [`0480-pg_query.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0480-pg_query.yml) | `pg_query` | 查询统计；要求 `extension:pg_stat_statements` |
| [`0510-pg_vacuuming.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0510-pg_vacuuming.yml) | `pg_vacuuming` | 仅主库的 VACUUM 进度；PG18+ 包含 `delay_time` |
| [`0520-pg_indexing.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0520-pg_indexing.yml) | `pg_indexing` | 仅主库的 `CREATE INDEX` 进度 |
| [`0530-pg_clustering.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0530-pg_clustering.yml) | `pg_clustering` | 仅主库的 `CLUSTER` 与 `VACUUM FULL` 进度 |
| [`0540-pg_backup.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0540-pg_backup.yml) | `pg_backup` | PG13+ 基础备份进度 |
| [`0610-pg_db.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0610-pg_db.yml) | `pg_db` | 各数据库统计；PG18+ 并行工作进程计数 |
| [`0620-pg_db_confl.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0620-pg_db_confl.yml) | `pg_db_confl` | 备库数据库冲突计数 |
| [`0640-pg_pubrel.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0640-pg_pubrel.yml) | `pg_pubrel` | 发布与发布关系数量 |
| [`0650-pg_subrel.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0650-pg_subrel.yml) | `pg_subrel` | 按状态汇总订阅关系 |
| [`0660-pg_vacuum_score.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0660-pg_vacuum_score.yml) | `pg_vacuum_score` | PG19 `pg_stat_autovacuum_scores` 自动清理评分摘要 |
| [`0700-pg_table.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0700-pg_table.yml) | `pg_table` | 每表统计；PG18+ 维护时间与新页面更新计数 |
| [`0710-pg_index.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0710-pg_index.yml) | `pg_index` | 每索引统计 |
| [`0720-pg_func.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0720-pg_func.yml) | `pg_func` | 函数执行统计 |
| [`0730-pg_seq.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0730-pg_seq.yml) | `pg_seq` | 序列指标 |
| [`0740-pg_relkind.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0740-pg_relkind.yml) | `pg_relkind` | 按关系类型统计对象数量 |
| [`0750-pg_defpart.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0750-pg_defpart.yml) | `pg_defpart` | 默认分区元组数量 |
| [`0810-pg_table_size.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0810-pg_table_size.yml) | `pg_table_size` | 每表大小；在超大模式中可能较慢 |
| [`0820-pg_table_bloat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0820-pg_table_bloat.yml) | `pg_table_bloat` | 默认禁用；要求辅助视图 `pg_table_bloat` |
| [`0830-pg_index_bloat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0830-pg_index_bloat.yml) | `pg_index_bloat` | 默认禁用；要求辅助视图 `pg_index_bloat` |
| [`0910-pgbouncer_list.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0910-pgbouncer_list.yml) | `pgbouncer_list` | 从管理数据库获取 PgBouncer 列表指标 |
| [`0920-pgbouncer_database.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0920-pgbouncer_database.yml) | `pgbouncer_database` | PgBouncer 数据库指标，含版本分支 |
| [`0930-pgbouncer_stat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0930-pgbouncer_stat.yml) | `pgbouncer_stat` | PgBouncer 各数据库统计，含版本分支 |
| [`0940-pgbouncer_pool.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0940-pgbouncer_pool.yml) | `pgbouncer_pool` | PgBouncer 连接池指标，含版本分支 |
| [`1000-pg_wait_event.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/1000-pg_wait_event.yml) | `pg_wait_event`, `pg_wait_event_1s` | 等待事件采样；要求 `extension:pg_wait_sampling` |
| [`1800-pg_tsdb_hypertable.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/1800-pg_tsdb_hypertable.yml) | `pg_tsdb_hypertable` | 默认禁用；要求 TimescaleDB 及其信息模式 |
| [`1900-pg_citus.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/1900-pg_citus.yml) | `pg_citus_node` | Citus 工作节点/协调节点清单；要求 `extension:citus` |
| [`2000-pg_heartbeat.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/2000-pg_heartbeat.yml) | `pg_heartbeat` | 默认禁用；要求 `postgres` 库中的 `monitor` 心跳表 |
{.full-width}

## 启用前先看计划

不要把 58 个文件理解成 58 条无条件执行的查询。规划器会根据 PostgreSQL 或 PgBouncer 版本、恢复角色、目标数据库、扩展、模式、用户名与谓词结果筛选分支。调优前先检查真实计划：

```bash
curl -fsS http://127.0.0.1:9630/explain
curl -fsS http://127.0.0.1:9630/explain | jq '.[] | {name, status, reason}'
```

默认禁用的采集器必须经过有意识的审核。`pg_origin`、`pg_shmem`、两个膨胀采集器、TimescaleDB 采集器和 `pg_heartbeat` 都需要额外权限、辅助对象、特定扩展或明确的写入/读取流程，因此不会进入通用默认计划。

## 基数与开销

每对象和每查询采集器是主要的基数来源。在大规模环境中启用前重点检查：

- `pg_table`、`pg_index`、`pg_func`、`pg_seq` 会为每个对象产生一组或多组时序。
- `pg_query` 的规模随 `pg_stat_statements` 保留的归一化语句数量增长。
- `pg_table_size`、`pg_table_bloat`、`pg_index_bloat` 在关系很多时可能成本较高。
- 等待事件采样依赖扩展，并可能产生随负载变化的维度。

用采集器 `ttl` 缓存高成本结果，设置符合实际的单采集器 `timeout`，并让抓取间隔大于最慢采集器的预期耗时。变更前后都应比较 `/metrics` 的耗时与时序数量，不能只凭“配置验证通过”判断生产安全性。

## 安全定制

把本地覆盖放在独立配置目录中，不要直接修改生成的单体文件。只复制最小相关文件，确保所有顶层分支名全局唯一、版本范围不重叠，然后执行：

```bash
pg_exporter --config=/path/to/collectors --dry-run
PG_EXPORTER_CONFIG=/path/to/collectors pg_exporter
curl -fsS http://127.0.0.1:9630/explain
curl -fsS http://127.0.0.1:9630/metrics >/dev/null
```

采集器模式、查询到指标的映射、标签、谓词、缓存、超时与直方图规则详见[采集器配置](/zh/config/)。
