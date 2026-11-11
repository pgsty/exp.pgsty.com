---
title: "兼容性"
linkTitle: "兼容性"
description: "支持的 PostgreSQL 与 PgBouncer 版本、发布产物、体系结构与部署约束"
weight: 40
icon: fa-solid fa-layer-group
categories: [参考]
---

按运行主机选择安装包，按数据库版本选择采集配置，再安装所需的视图或扩展。本页说明 v{{< param version >}} 随附的默认配置，以及单独维护的 legacy 配置的兼容范围。

## 数据库目标 {#database-targets}

| 目标 | 状态 | 配置 |
|:---|:---|:---|
| PostgreSQL 10-18 | 默认支持 | `pg_exporter.yml` / `config/` |
| PostgreSQL 19 | 已包含版本专用分支 | 默认配置；在实际服务器构建上检查查询结果 |
| PostgreSQL 9.1-9.6 | 历史遗留支持（非主干支持） | main 上维护的 `legacy/pg_exporter.yml` / `legacy/config/` |
| PostgreSQL 9.0 及更早版本 | 不支持 | — |
| PgBouncer 1.8+ | 按版本选择采集器 | `0910`-`0940` 采集器文件；连接管理数据库 |
{.full-width .wide .expand}

PostgreSQL 19 分支覆盖恢复、锁、自动清理评分、WAL、订阅、接收器与复制槽。采集器按服务器版本号选择分支；首次抓取后，检查 `/stat`，确认查询与实际服务器构建匹配。

内置 PgBouncer 采集器要求 1.8 或更高版本。1.8 调整了查询所用的 `SHOW STATS` 字段。最新配置分支未设版本上限；升级 PgBouncer 后，结合[上游变更日志](https://www.pgbouncer.org/changelog.html)检查采集结果。

## 发布验证 {#release-validation}

v1.6.0 发布基线已以非超级用户通过 PostgreSQL 9.2–9.6（legacy 配置）、10–18 与 19 RC1（默认配置）的主库采集，以及 PgBouncer 1.26.1 实测。PG10–13 使用文档要求的订阅 OID 授权；另验证了物理备库晋升、断连恢复、并发采集／健康检查／重载、HTTPS 认证、软件包安装及从 1.5.0 升级。PG19 证据对应 RC1。后续使用 `282e19d` 的 legacy 配置（已包含在 v1.6.1 源码标签中）补充验证了 PostgreSQL 9.1–9.6 中有 TOAST 和无 TOAST 的表，获取方式见[安装说明](/zh/install/#compatibility)。

v1.6.1 维护版本通过了完整 race 测试与 Go 1.21 HTTP mux 测试、模块与生成配置一致性门禁、六平台交叉编译、RPM／DEB 软件包安装与校验和验证（Debian 12 与 Rocky Linux 9）、公开多架构 Docker 镜像的 CA／TLS／文件内容与流复制主库抓取验证，以及非超级用户 `monitor` 在 PostgreSQL 9.1–9.6（`legacy/pg_exporter.yml`）、PostgreSQL 10–18 与 19 RC1 主库（默认 `pg_exporter.yml`）、PostgreSQL 18 与 19 RC1 物理流复制备库及 PgBouncer 1.26.1 上的实机矩阵验收（全部零查询报错）。Windows、Linux ppc64le 与 Intel macOS 制品仅做构建与校验和检查，没有实际运行验收。上述验证不代表覆盖每种扩展、服务器构建或生产负载。

## 指标、仪表盘与告警兼容性 {#metric-compatibility}

升级 Exporter 和升级 PostgreSQL 大版本，可能改变指标契约的不同部分。以下对照以 [`v1.4.1`](https://github.com/pgsty/pg_exporter/tree/v1.4.1/config)、[`v1.5.0`](https://github.com/pgsty/pg_exporter/tree/v1.5.0/config)、[`v1.6.0`](https://github.com/pgsty/pg_exporter/tree/v1.6.0/config) 与 [`v1.6.1`](https://github.com/pgsty/pg_exporter/tree/v1.6.1/config) 标签中的内置 SQL 采集器为准，包含各列的 `rename` 映射；列出的是实际导出的指标名，不只是 PostgreSQL 视图列名或 YAML 文件名。自定义采集器与业务告警规则仍需单独检查。

### Exporter v1.6.0 → v1.6.1 {#exporter-161-metrics}

内置 SQL 指标名、标签键、类型、分桶、HTTP 路由与命令行参数均未改变。默认配置仍包含 58 个 YAML 文件、96 个分支、59 个命名空间和 460 个去重指标定义。v1.6.1 包含以下 SQL 取值与运行时边界修复：

| 接口／指标 | 变化 | 升级处理 |
|:---|:---|:---|
| `pg_table_age` 与 `pg_table` 扫描／元组汇总 | 分区父表（`relkind = 'p'`，`relfrozenxid = 0`）的 `age` 报告为 `0` 而非 `2147483647`；`tbl_scan`、`tup_read`、`n_tup_mod` 对可空列做 `COALESCE`，修复无索引表（`idx_scan IS NULL`）或无统计行关系求和退化为 `0` 的问题（`pg_table_10` 元组 Gauge 同步补齐 `default: 0`） | 更新 YAML；冻结年龄告警不再对分区父表产生误报 |
| `pg_table_size_*` | 在 `pg_catalog`、`information_schema`、`pg_toast` 之外排除临时模式（`pg_temp*`） | 更新 YAML，跳过其他会话的瞬态临时表 |
| `pg_activity_max_*_duration` | 通过 `greatest(..., 0)` 将亚毫秒级负数耗时截断为 `0` | 更新 YAML |
| `pg_tsdb_hypertable_*` | 使用 `format('%I.%I', ...)::regclass` 安全引用模式名与超表名 | 在大小写敏感或特殊字符命名上启用 TimescaleDB 采集器时更新 YAML |
| 重复标签隔离与子库连接池回收 | 重复的 `(指标, 标签)` 行仅使所属采集器失败，不再中断整次 `/metrics` 响应；自动发现移除数据库或重载时关闭旧子库连接池 | 升级二进制（以及支持 `systemctl reload pg_exporter` 的服务单元文件） |
{.full-width .wide .expand}

### Exporter v1.5.0 → v1.6.0 {#exporter-160-metrics}

在相同 PostgreSQL 版本上，内置 SQL 指标名、标签键、类型与单位不变，仍有 460 个去重指标定义。以下行为与标签取值发生变化：

| 接口／指标 | 变化 | 升级处理 |
|:---|:---|:---|
| `pg_vacuuming_*`、`pg_indexing_*`、`pg_clustering_*` | 其他数据库的用户关系在 `relname` 中使用数字 OID；当前库与系统目录仍解析名称 | 更新 YAML；面板保留 `datname`、`pid`，接受新的标签取值 |
| `/up` 与角色路由 | 初始化后只由健康探测更新 HTTP 状态 | 数据库可达时可能返回 200，而 fatal 采集器让 `pg_up` 为 0；按告警目的选择信号 |
| 抓取错误计数 | 中断轮次不计作目标错误 | 单个查询失败查看查询级计数与日志，详见 [API](/zh/api/) |
| `/metrics` 并发 | 最多接纳两个请求，等待可取消，超额或采集预算耗尽返回 503 | 控制并发抓取者数量并检查时间预算 |
| PgBouncer 连接池 | 最大连接数由一个增为两个 | 为串行采集与后台探测各留一个连接 |
{.full-width .wide .expand}

从更早版本升级时，上文 v1.6.0 以及下文 v1.5.0 和 PostgreSQL 大版本迁移规则仍然适用。v1.6.1 不包含 `snort` 的实验组件。

### Exporter v1.4.1 → v1.5.0 {#exporter-150-metrics}

保持 PostgreSQL 版本不变时，**内置 SQL 指标没有新增、删除或改名**，指标类型和单位也不变。不过，以下变化仍需检查仪表盘与告警：

| 指标 | v1.5.0 配置的变化 | 迁移操作 |
|:---|:---|:---|
| `pg_sub_*` | 每条样本增加订阅归属数据库的 `datname` 标签；`pg_sub_id` 仍为 Gauge。 | 连接与按订阅聚合时，保留 `datname`、`subname` 及目标身份。仅按 `subname` 连接可能因跨库同名订阅产生歧义。新标签集会产生新时序，也可能重置告警的 pending 计时。 |
| `pg_recv_state` | 保留 `streaming=0`、`stopping=4`、`connecting=5`（PG19+）及未知／NULL `=-1`；新增 `starting=6`、`waiting=7`、`restarting=8`、`stopped=9`。这四种状态此前落入 `-1`。 | 更新 Grafana 值映射，以及只识别 `-1` 或旧 0–5 范围的规则。编码 1–3 保留；旧说明中的 `startup`、`catchup`、`backup` 是误用于接收器的发送端状态。没有接收器行时仍不输出样本。 |
| `pg_subrel_count`、`pg_pubrel_count` | HELP 文本澄清已有的表／序列统计口径；本版未改变它们的 SQL、标签或数值。 | 不要将两者当作同一对象集合来比较；PG19 的行为见下表。 |
{.full-width .wide .expand}

这些修正需要同时部署新版 YAML 和二进制。PG10–13 的订阅采集器还需要[订阅 OID 授权](/zh/collectors/#subscription-identity-and-receiver-states)，否则查询失败，指标会缺失。兼容性决策详见[复制采集器设计记录](/zh/design/replication-collector-contracts/)。

### 使用 v1.5.0 配置，PostgreSQL 18 → 19 {#postgresql-19-metrics}

**从 PG18 分支切换到 PG19 分支，不会删除或改名 PG18 分支已有的指标。** PostgreSQL 19 采集器支持最早随 [Exporter v1.3.0](/zh/release/v1.3.0/) 发布，以下行为由 v1.5.0 继承，与上面的标签和接收器修正属于不同变化。PostgreSQL 验收证据对应 19 RC1。

| 指标或指标族 | PG19 行为 | 对仪表盘／告警的影响 |
|:---|:---|:---|
| `pg_sub_sync_error_count` | 保留旧名，值为 `sync_table_error_count + sync_seq_error_count`；PG15–18 只统计表的初始同步错误。 | 原有“所有同步错误”告警仍有指标可查，但现在也包含序列同步错误。需要复核阈值：名称未变，统计范围扩大。 |
| `pg_sub_sync_table_error_count`、`pg_sub_sync_seq_error_count` | 新增两个 Counter，分别统计表和序列同步错误。 | PG19 上只关注表同步错误时，使用表计数器。不要再将这两个指标加到 `pg_sub_sync_error_count` 上，否则重复计数。 |
| `pg_sub_confl_*`、`pg_sub_reset_time`、`pg_sub_has_worker` | 新增八个冲突 Counter、统计重置时间戳 Gauge 和 apply leader worker 存在标记 Gauge。PG19 查询以订阅统计为起点，即使没有 apply worker 也保留订阅行。 | PG19 上对预期运行的订阅可检查 `pg_sub_has_worker == 0`；仍有 `pg_sub_id` 不代表 worker 正常运行。须排除主动禁用的订阅。 |
| `pg_subrel_count` | 同时统计表和序列，按 `datname`、`subname`、`state` 分组。序列状态为 `i`／`r`，表状态为 `i`／`d`／`f`／`s`／`r`。 | 原来标作“表数量”的面板可能混入序列，且没有关系类型标签可用于拆分。`pg_pubrel_count` 仍只统计表；空发布或仅含序列的发布没有时序。 |
| `pg_wal_fpi_bytes` | 新增全页镜像 WAL 字节数 Counter。 | 属于新增指标。`pg_wal_bytes` 和 `pg_wal_fpi` 的名称与含义保持不变，新指标不替代它们。 |
| `pg_lock_stat_waits`、`pg_lock_stat_wait_time`、`pg_lock_stat_fastpath_exceeded` | 新增按 `locktype` 分组的 Counter；等待时间导出为秒。等待统计只计入超过 `deadlock_timeout` 的等待。 | 补充当前锁分布指标 `pg_lock_count`，不替代它，也不统计所有短暂锁等待。 |
| `pg_recovery_state_*` | 新增九个恢复状态指标，只在备库选择该采集器。 | 补充原有 `pg_recovery_*`；主库没有这些指标属于正常情况。使用 `rate()` 前须确认具体指标类型。 |
| `pg_vacuum_score_*` | 新增十一个 Gauge，按数据库汇总 autovacuum 评分和候选数量，只在主库选择该采集器。 | 属于新增指标；备库或旧版本缺失属于正常情况。这些是当前评分／数量，不是累计事件 Counter。 |
{.full-width .wide .expand}

精确定义见发布标签中的[订阅](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0260-pg_sub.yml)、[订阅关系](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0650-pg_subrel.yml)、[WAL](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0400-pg_wal.yml)、[锁](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0470-pg_lock_stat.yml)、[恢复](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0370-pg_recovery_state.yml)与[自动清理](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0660-pg_vacuum_score.yml)采集器。

对于使用 v1.5.0 配置的 PG15–19 混合环境，以下表达式保持 **只统计表同步错误** 的速率口径。PG19 指标存在时优先使用左侧；两侧标签和目标选择条件须一致：

```promql
rate(pg_sub_sync_table_error_count[5m])
or
rate(pg_sub_sync_error_count[5m])
```

### 从 PG17 或更早版本升级 {#older-postgresql-metrics}

直接升到 PG19 还会跨越较早 PostgreSQL 版本的指标变化。下列旧名在 v1.5.0 配置采集 PG19 时已不存在，但它们的消失 **并非 Exporter v1.5.0 或 PostgreSQL 19 新引入**。

| 旧指标 | 首次不再输出的 PG 版本 | 替代指标或处理方式 |
|:---|:---|:---|
| `pg_bgwriter_checkpoints_timed` | PG17 | `pg_checkpointer_timed` |
| `pg_bgwriter_checkpoints_req` | PG17 | `pg_checkpointer_req` |
| `pg_bgwriter_checkpoint_write_time` | PG17 | `pg_checkpointer_write_time`（秒） |
| `pg_bgwriter_checkpoint_sync_time` | PG17 | `pg_checkpointer_sync_time`（秒） |
| `pg_bgwriter_buffers_checkpoint` | PG17 | `pg_checkpointer_buffers_written` |
| `pg_bgwriter_buffers_backend`、`pg_bgwriter_buffers_backend_fsync` | PG17 | 按所需后端 `type`、`object`、`context` 检查 `pg_io_writes`／`pg_io_fsyncs`。它们不是直接改名：I/O 操作数与缓冲区数量的范围、单位未必相同。 |
| `pg_wal_write` | PG18 | `pg_io_writes{object="wal"}` |
| `pg_wal_sync` | PG18 | `pg_io_fsyncs{object="wal"}` |
| `pg_wal_write_time` | PG18 | `pg_io_write_time{object="wal"}`（秒） |
| `pg_wal_sync_time` | PG18 | `pg_io_fsync_time{object="wal"}`（秒） |
{.full-width .wide .expand}

v1.5.0 配置在 PG10–16 上也通过旧 SQL 列的别名提供上述 `pg_checkpointer_*` 指标，混合版本仪表盘可优先使用这些名称。PG18+ 还提供表示已完成检查点的 `pg_checkpointer_done`；`timed`、`req` 统计计划／请求量，不应当作已完成总量。PG17+ 的检查点统计按各指标定义包含 restartpoint 活动。

WAL I/O 转到带有 `type`、`object`、`context` 维度的视图，不能只替换名字。例如，PG18+ 按目标汇总的 WAL 写操作速率为：

```promql
sum by (job, instance) (rate(pg_io_writes{object="wal"}[5m]))
```

按实际环境保留额外的集群／目标标签，核对后端范围与计时开关后再比较历史值。PG18+ 还新增 `pg_io_read_bytes`、`pg_io_write_bytes`、`pg_io_extend_bytes`；计算字节吞吐量时应使用这些指标，不再假定每次操作对应固定字节数。参见发布标签中的 [I/O](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0300-pg_io.yml)、[后台写进程](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0330-pg_bgwriter.yml)、[检查点进程](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0331-pg_checkpointer.yml)定义与 [PostgreSQL 18 迁移说明](https://www.postgresql.org/docs/18/release-18.html)。

### 避免指标缺失让告警静默 {#missing-metric-alerts}

Prometheus 告警表达式返回空向量时，不会产生告警实例。HTTP 200、Prometheus `up == 1` 或 `pg_up == 1`，都不能证明每个采集器和告警表达式仍然正常。参见 [Prometheus 告警求值规则](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)。

1. 合并并部署配套 YAML，保留本地定制。对每种版本与角色选择代表性目标，抓取 `/metrics`，检查 `/explain`、`/stat`、`pg_exporter_query_scrape_error_count` 和日志中的查询错误。
2. 执行实际仪表盘、记录规则和告警表达式，检查名称、标签连接、单位、状态映射与返回时序，并等待 `rate()` 窗口积累足够样本。空结果不等于健康的零值。
3. 分别用正常数据和缺失时序测试告警规则（`promtool check rules` 检查语法，`promtool test rules` 可检查行为）。Exporter 测试通过不等于下游仪表盘已经验证。
4. 按目标检查预期存在的关键指标，同时限定服务器版本、角色与已配置对象。不要用无条件 `or vector(0)` 掩盖输入缺失。

例如，假设 `job="pg19"` 只包含预期启用内置 WAL 采集器的 PG19 目标，以下规则可逐个发现数据库健康但缺少 `pg_wal_bytes` 的目标：

```yaml
groups:
  - name: pg-exporter-compatibility
    rules:
      - alert: PgWalMetricMissing
        expr: (pg_up{job="pg19"} == 1) unless on (job, instance) pg_wal_bytes{job="pg19"}
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Expected WAL metric is missing from a healthy PostgreSQL target"
```

按实际目标身份调整选择器与匹配标签，并分别监控 `up` 和 `pg_up` 故障。已知的单个目标也可使用 [`absent_over_time()`](https://prometheus.io/docs/prometheus/latest/querying/functions/#absent_over_time)。仅对整个集群执行 `absent(metric)`，无法发现其他目标仍有数据时的单目标缺失。同理，`pg_recv_state != 0` 无法发现已经消失的接收器行；预期持续流复制的备库还需要单独检查接收器是否存在。

## v{{< param version >}} 发布产物 {#release-artifacts}

| 产物 | 操作系统 | 体系结构 |
|:---|:---|:---|
| Tarball | Linux | amd64、arm64、ppc64le |
| Tarball | macOS | amd64、arm64 |
| Tarball | Windows | amd64 |
| RPM | RHEL 兼容 Linux | x86_64、aarch64、ppc64le |
| DEB | Debian/Ubuntu 兼容 Linux | amd64、arm64、ppc64le |
| Docker 镜像 | Linux 容器 | amd64、arm64 |
{.full-width .wide .expand}

发布压缩包包含二进制、合并后的默认配置、许可证、默认环境文件与 systemd 单元。PostgreSQL 9.1–9.6 配置属于历史遗留维护（非主干支持），在 `main` 分支的 `legacy/` 下单独维护，不包含在二进制压缩包中，也不应从旧发布标签获取；获取方式见[安装说明](/zh/install/#compatibility)。macOS 与 Windows 产物适合开发或连接远端目标；软件包提供的服务集成只适用于 Linux。

> [!NOTE] v1.4.1 起的 RPM 包名
> 官方 RPM 包名与产物前缀改为 `pg-exporter`。新包为旧的 `pg_exporter` 名称声明了 `Provides` 与 `Obsoletes`，因此可以直接升级。可执行文件与配置名仍为 `pg_exporter` 和 `/etc/pg_exporter.yml`。

## 容器约束 {#container-constraints}

镜像基于 `scratch`，包含系统 CA 证书包与许可证，但没有 shell。公共受信任证书可使用内置根证书；使用私有 CA 且启用 `sslmode=verify-ca` 或 `verify-full` 时，仍需挂载私有 CA 并设置 `sslrootcert`。

## 采集器级前置条件 {#collector-level-requirements}

采集器还会按目标数据库的实际条件选择：

- `primary` / `replica` 标签按恢复角色限制执行。
- `dbname:`、`extension:`、`schema:` 与 `username:` 标签要求对应事实匹配。
- 谓词查询可以执行额外的运行时检查。
- 默认关闭的采集器（`skip: true`）必须显式启用。
- 表/索引膨胀等辅助视图采集器需要相应视图与权限。

先抓取一次 `/metrics`，再通过 [`/explain`](/zh/api/#get-explain) 查看当前采集计划，通过 `/stat` 检查查询结果。每个文件的前置条件参见[内置采集器](/zh/collectors/)。
