---
title: "采集器配置"
linkTitle: "配置参考"
description: "声明式 YAML 采集器格式与执行模型的完整参考"
weight: 90
icon: fa-solid fa-code
categories: [参考]
---

YAML **采集器** 定义 SQL 查询、输出指标和执行条件。本页适用于稳定版 **v{{< param version >}}**。进程参数和环境变量见[命令参考](/zh/cmd/)。

配置可以是单个 YAML 文件或一个目录。默认 `pg_exporter.yml` 由 [`config/`](https://github.com/pgsty/pg_exporter/tree/v1.5.0/config) 目录下的 57 个采集器文件和 1 个配置参考文件合并而成。

--------

## 配置加载

PG Exporter 按以下顺序搜索配置：

1. 命令行参数：`--config=/path/to/config`
2. 环境变量：`PG_EXPORTER_CONFIG=/path/to/config`
3. 当前目录：`./pg_exporter.yml`
4. 系统配置文件：`/etc/pg_exporter.yml`
5. 系统配置目录：`/etc/pg_exporter/`

目录模式说明：

- 仅加载该目录下的 `.yml` / `.yaml` 文件（非递归）
- 按文件名字典序合并；同名采集器以后加载者覆盖先前定义
- 若其他文件提供了有效采集器，加载器会跳过无效文件并记录警告。目录中有 YAML 文件但没有有效采集器定义时，加载失败
- 选中的文件或目录就是完整配置，不会叠加其他标准路径。显式指定的路径加载失败时不会回退

--------

## 简单的 Gauge 采集器

先按[快速上手](/zh/start/#run-and-verify)设置包含目标和凭据的 `PG_EXPORTER_URL`。将下列内容保存为 `connections.yml`；它导出连接总数及各状态的连接数。

```yaml
pg_connections:
  desc: "实例连接数"
  query: |
    SELECT
      count(*) as total,
      count(*) FILTER (WHERE state = 'active') as active,
      count(*) FILTER (WHERE state = 'idle') as idle,
      count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
    FROM pg_stat_activity
    WHERE pid != pg_backend_pid()
  tags: [cluster]
  ttl: 1
  metrics:
    - total: {usage: GAUGE, description: "总连接数"}
    - active: {usage: GAUGE, description: "活跃连接数"}
    - idle: {usage: GAUGE, description: "空闲连接数"}
    - idle_in_transaction: {usage: GAUGE, description: "事务中空闲连接数"}
```

先校验配置，再以前台进程运行：

```bash
pg_exporter --dry-run --config=./connections.yml
pg_exporter --config=./connections.yml
```

在另一个终端检查输出：

```bash
curl -fsS http://127.0.0.1:9630/metrics | grep '^pg_connections_'
```

此文件只包含示例采集器。要在默认指标上增加自己的指标，见[自定义采集器](#自定义采集器)。

--------

## 采集器结构

每个顶层键标识一个采集器分支。下面展示可用字段，使用时将 SQL 和列名替换为实际查询：

```yaml
collector_branch_name:           # 此采集器的唯一标识符
  name: metric_namespace         # 指标前缀（默认为分支名称）
  desc: "采集器描述"             # 人类可读的描述
  query: |                       # 要执行的 SQL 查询
    SELECT column1, column2
    FROM table

  # 执行控制
  priority: 100                  # 致命/非致命分组内，数值越小越先执行
  ttl: 10                        # 缓存生存时间（秒）
  timeout: 0.1                   # 查询超时（秒）
  fatal: false                   # 为 true 时，错误会停止该数据库的后续采集
  skip: false                    # 如果为 true，禁用此采集器

  # 版本兼容性
  min_version: 100000            # 最小 PostgreSQL 版本（包含）
  max_version: 999999            # 最大 PostgreSQL 版本（不包含）

  # 执行标签
  tags: [cluster, primary]       # 执行条件

  # 谓词查询（可选）
  predicate_queries:
    - name: "check_function"
      ttl: 60                    # 谓词结果的独立缓存时间，单位秒
      predicate_query: |
        SELECT EXISTS (...)

  # 指标定义
  metrics:
    - column_name:
        usage: GAUGE             # GAUGE、COUNTER、HISTOGRAM、LABEL 或 DISCARD
        rename: metric_name      # 可选：重命名指标
        description: "帮助文本"   # 指标描述
        default: 0               # NULL 时的默认值
        scale: 1000              # 值的缩放因子
        # usage 为 HISTOGRAM 时，还需配置 bucket: [1, 10, 100]
```

配置校验约束：

- `query` 和每个 `predicate_query` 都必须包含 SQL；主查询和谓词的 TTL 必须大于或等于零
- 每个 `metrics` 列表项必须且只能定义一个列映射，源列名不能重复
- 每个采集器至少要有一个 `GAUGE` / `COUNTER` / `HISTOGRAM` 列
- `usage` 支持 `GAUGE` / `COUNTER` / `HISTOGRAM` / `LABEL` / `DISCARD`，不区分大小写
- `HISTOGRAM` 列必须定义 `bucket`：有限、严格递增的桶上界列表，`+Inf` 桶自动追加
- 指标名、标签名会在加载阶段进行 Prometheus 规则校验，非法配置会直接报错
- 启动和重载时会检查固定标签与查询标签的冲突。开启内置指标时，`datname` 和 `query` 也是保留名称。任一已配置采集器使用 `HISTOGRAM` 时，固定标签不能叫 `le`
- SQL 结果必须包含所有 `LABEL` 和 `HISTOGRAM` 列，即使返回零行也一样。缺少这些列会拒绝整个采集器结果。缺失的 `GAUGE` 或 `COUNTER` 列会被记录到日志并略过
- 如果使用单行内联 `metrics` 写法，`description` 建议始终使用双引号包裹，避免 YAML 歧义

--------

## 核心配置元素

### 采集器分支名称

顶层键标识分支，`name` 设置指标前缀：

```yaml
pg_stat_database:  # 必须唯一
  name: pg_db      # 实际的指标命名空间
```

不同服务器版本的分支可以使用相同 `name`，但版本范围和标签应保证同一指标序列只由一个分支生成。规划器会选中所有符合条件的分支，不会按名称自动选出一个。

`priority` 控制执行顺序，数值越小越先执行。致命采集器先于非致命采集器执行。目录模式中，未指定的优先级为 `100 +` 成功加载文件的序号；单文件中则保留为零。有顺序要求时，请设置不同的优先级。

### 查询定义

检索指标的 SQL 查询：

```yaml
query: |
  SELECT
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit
  FROM pg_stat_database
  WHERE datname NOT IN ('template0', 'template1')
```

### 指标类型

将每个结果列声明为数值、标签或忽略列。标量指标名为 `<采集器名称>_<列名>`。列的 `rename` 修改指标后缀或标签名；列的 `name` 修改用于查找 SQL 结果的源列名。

| 用途          | 描述                                        | 示例     |
|-------------|-------------------------------------------|--------|
| `GAUGE`     | 可上下波动的瞬时值                                 | 当前连接数  |
| `COUNTER`   | 累计值；源统计重置时可归零                                  | 总事务数   |
| `HISTOGRAM` | 快照直方图，派生 `_bucket` / `_count` / `_sum` 序列 | 事务年龄分布 |
| `LABEL`     | 用作 Prometheus 标签                          | 数据库名称  |
| `DISCARD`   | 忽略此列                                      | 内部值    |
{.full-width}

### 直方图列（HISTOGRAM）

`HISTOGRAM` 从 v1.4.0 起可用，按标签值将观测分组，每个非 NULL 值贡献一次观测。
输出为三组 Gauge 指标：`<采集器>_<列名>_bucket`、`_count` 和 `_sum`。
桶在当前快照内累计计数，并包含 `le="+Inf"`：

```yaml
pg_xact_age:
  name: pg_xact_age
  desc: "开放事务年龄分布直方图"
  query: |
    SELECT datname,
           greatest(0, extract(epoch FROM now() - xact_start)) AS seconds
    FROM pg_stat_activity
    WHERE pid <> pg_backend_pid() AND backend_type = 'client backend'
      AND datname IS NOT NULL AND xact_start IS NOT NULL;
  ttl: 10
  min_version: 100000
  tags: [cluster]
  metrics:
    - datname: {usage: LABEL, description: "数据库名称"}
    - seconds:
        usage: HISTOGRAM
        bucket: [1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000]
        description: "开放事务年龄快照（秒）"
```

使用注意：

- 采集器刷新缓存时重建分布。三组指标的类型均为 `gauge`，值都可以下降。
  对桶直接使用 `histogram_quantile()`，用当前 `_sum / _count` 计算均值。
  不要对这些快照序列使用 `rate()` 或 `increase()`
- SQL `NULL` 默认不计入观测，配置 `default` 后按默认值计入。没有观测的标签组不输出直方图序列。无法转换的值、NaN 或无穷值会使整个采集器结果失败
- `scale` 在分桶前应用于观测值；与标量列一致，时间戳与布尔值不受 `scale` 影响
- 默认配置包中的 [`pg_xact_age`](https://github.com/pgsty/pg_exporter/blob/v1.5.0/config/0450-pg_xact_age.yml) 采集器即为参考实现

上例的 95 分位数可以这样计算：

```promql
histogram_quantile(0.95, pg_xact_age_seconds_bucket)
```

### 缓存控制（TTL）

`ttl` 参数控制结果缓存：

```yaml
# 快速查询 - 最小缓存
pg_stat_activity:
  ttl: 1  # 缓存 1 秒

# 昂贵查询 - 较长缓存
pg_table_bloat:
  ttl: 3600  # 缓存 1 小时
```

`ttl` 默认为 0，每次抓取都会刷新。需要减少 SQL 执行次数时，将 TTL 设为大于抓取间隔的值；具体取值取决于能接受多旧的指标。`--disable-cache` 会强制刷新主查询结果。

刷新失败时会清除旧结果。错误或谓词跳过的结果会保留到主查询 TTL 到期。谓词结果还可以设置独立的缓存时间。

### 超时控制

防止查询运行时间过长：

```yaml
timeout: 0.1   # 100 ms；未配置或设置为 0 时也使用此值
timeout: 1.0   # 1 秒
timeout: -1    # 关闭该采集器的查询超时
```

超时覆盖所有谓词和主查询的总执行时间。将其设为高于正常查询耗时、低于抓取时间预算的值。连接预检查使用独立的 `--connect-timeout` 参数，单位为毫秒。

缓存 TTL 和超时配置拒绝 NaN、无穷大以及会使 Go `time.Duration` 溢出的正数。缓存 TTL 仍须非负；有限的负超时仍表示关闭查询期限。

### 版本兼容性

控制哪些 PostgreSQL 版本可以运行此采集器：

```yaml
min_version: 100000  # PostgreSQL 10.0+
max_version: 140000  # 低于 PostgreSQL 14.0
```

`min_version` 包含边界，`max_version` 不包含边界。未配置或为零时，该端不设限制。`skip` 和 `fatal` 默认为 `false`。

版本号使用 PostgreSQL 内部 `server_version_num` 规则：

- `100000` 表示 10.0
- `130002` 表示 13.2
- `160001` 表示 16.1
- `190000` 表示 19.0
- `90600` 表示 9.6（Legacy 配置场景）

--------

## 执行模型

采集器按以下步骤工作：

1. **规划**：首次抓取或计划失效后，检查目标类型、版本、标签和 `skip`，选中所有符合条件的分支。`/explain` 展示主连接的选中的采集器，调试日志记录分支被排除的原因。
2. **采集**：缓存有效时返回缓存结果；到期后执行谓词和主查询，共用一个超时。完整结果转换成功后才输出指标。
3. **处理失败**：普通采集器报错时不输出该组结果，并增加其查询错误计数。致命采集器报错后，停止该数据库的后续采集，并将该数据库本轮抓取记为失败。主连接目标失败时还会将 `pg_up` 设为 0，其他自动发现数据库仍可继续采集。

元数据预检成功后，连接用户名、Schema 集合或扩展集合变化也会触发重新规划。新增的符合条件采集器在下一次抓取生效；依赖被移除后，对应采集器不再选中。集合不变则保留计划和缓存；重新规划与重载一样会重置查询统计与缓存。

--------

## 标签系统

标签控制采集器的执行时机和位置：

### 内置标签

| 标签                    | 描述                   |
|-----------------------|----------------------|
| `cluster`             | 只在主连接执行，不在自动发现数据库的额外连接执行 |
| `primary` / `master` / `leader`  | 仅在主服务器上执行            |
| `standby` / `replica` / `slave` | 仅在从服务器上执行            |
| `pgbouncer`           | 仅用于 PgBouncer 连接     |
{.full-width}

`cluster` 不会协调不同 exporter 进程或 PostgreSQL 实例。采集器上的所有标签都必须满足。

### 前缀标签

| 前缀 | 示例 | 描述 |
|------|------|------|
| `dbname:` | `dbname:postgres` | 仅在特定数据库上执行 |
| `username:` | `username:monitor` | 仅使用特定用户时执行 |
| `extension:` | `extension:pg_stat_statements` | 仅当扩展已安装时执行 |
| `schema:` | `schema:public` | 仅当模式存在时执行 |
| `not:` | `not:slow` | 当导出器没有该标签时执行 |
{.full-width}

### 自定义标签

向导出器传递自定义标签：

```bash
pg_exporter --tag="production,critical"
```

然后在配置中使用：

```yaml
expensive_metrics:
  tags: [critical]  # 仅在有 'critical' 标签时运行
```

--------

## 谓词查询

在执行主查询之前进行条件检查：

```yaml
predicate_queries:
  - name: "检查 pg_stat_statements"
    predicate_query: |
      SELECT EXISTS (
        SELECT 1 FROM pg_extension
        WHERE extname = 'pg_stat_statements'
      )
```

每个谓词必须返回一个布尔类型列。一行 `true` 表示通过；`false`、NULL 或零行表示跳过主查询。多行结果、非布尔列或 SQL 错误会使采集器失败。所有谓词都通过后才执行主查询。

给谓词添加 `ttl: 60`，可以缓存其通过或跳过结果 60 秒。默认值为 0，在主查询每次刷新时重新检查。错误不会写入谓词缓存。`--disable-cache` 不会绕过谓词缓存。

--------

## 指标定义

### 基本定义

```yaml
metrics:
  - numbackends:
      usage: GAUGE
      description: "已连接的后端进程数"
```

### 高级选项

```yaml
metrics:
  - checkpoint_write_time:
      usage: COUNTER
      rename: write_time        # 重命名指标
      scale: 0.001              # 将毫秒转换为秒
      default: 0                # NULL 时使用 0
      description: "检查点写入时间（秒）"
```

--------

对 `GAUGE` 和 `COUNTER`，SQL NULL 默认转换为 `NaN`，可用 `default` 指定替代值。数值和默认值都会乘以 `scale`（默认 1）。时间戳转换为 Unix 秒数，布尔值转换为 0 或 1，两者不受缩放影响。NULL 标签转换为空字符串。

## 采集器组织

PG Exporter 自带预先组织好的采集器：

| 范围    | 类别        | 描述            |
|-------|-----------|---------------|
| 0000   | 文档        | 示例和文档         |
| 0100   | 基础        | 服务器信息、设置、元数据  |
| 0200   | 复制        | 复制、槽位、接收器     |
| 0300   | 持久化       | I/O、检查点、恢复   |
| 0400   | 活动        | WAL、连接、锁、查询       |
| 0500   | 进度        | Vacuum、索引创建进度 |
| 0600   | 数据库       | 每数据库统计        |
| 0700   | 对象        | 表、索引、函数       |
| 0800   | 可选        | 昂贵/可选指标       |
| 0900   | PgBouncer | 连接池指标         |
| 1000+ | 扩展        | 扩展特定指标        |
{.full-width .wide .expand}

--------

## 实际示例

### 带标签的 Counter

```yaml
pg_table_stats:
  desc: "表统计信息"
  query: |
    SELECT
      current_database() AS datname,
      schemaname,
      relname AS tablename,
      n_tup_ins,
      n_tup_upd,
      n_tup_del,
      n_live_tup,
      n_dead_tup
    FROM pg_stat_user_tables
  ttl: 10
  metrics:
    - datname: {usage: LABEL}
    - schemaname: {usage: LABEL}
    - tablename: {usage: LABEL}
    - n_tup_ins: {usage: COUNTER, description: "插入的元组数"}
    - n_tup_upd: {usage: COUNTER, description: "更新的元组数"}
    - n_tup_del: {usage: COUNTER, description: "删除的元组数"}
    - n_live_tup: {usage: GAUGE, description: "活跃元组数"}
    - n_dead_tup: {usage: GAUGE, description: "死亡元组数"}
```

### 版本特定采集器

此示例使用 PostgreSQL 14–17 的列。PostgreSQL 18 将 WAL 耗时统计移入 `pg_stat_io`，内置 `pg_wal` 采集器为此提供了不同分支。

```yaml
pg_wal_stats:
  desc: "WAL 统计信息（PG 14–17）"
  min_version: 140000
  max_version: 180000
  query: |
    SELECT
      wal_records,
      wal_bytes,
      wal_buffers_full,
      wal_write_time,
      wal_sync_time
    FROM pg_stat_wal
  ttl: 10
  tags: [cluster]
  metrics:
    - wal_records: {usage: COUNTER}
    - wal_bytes: {usage: COUNTER}
    - wal_buffers_full: {usage: COUNTER}
    - wal_write_time: {usage: COUNTER, scale: 0.001}
    - wal_sync_time: {usage: COUNTER, scale: 0.001}
```

### 扩展依赖采集器

此示例要求 PostgreSQL 13+ 的 `pg_stat_statements` 结构，且扩展所在模式已加入搜索路径。

```yaml
pg_stat_statements_metrics:
  desc: "查询性能统计"
  min_version: 130000
  tags: [cluster, "extension:pg_stat_statements"]
  query: |
    SELECT
      sum(calls) as total_calls,
      sum(total_exec_time) as total_time,
      sum(total_exec_time) / NULLIF(sum(calls), 0) as mean_time
    FROM pg_stat_statements
  ttl: 60
  metrics:
    - total_calls: {usage: COUNTER}
    - total_time: {usage: COUNTER, scale: 0.001}
    - mean_time: {usage: GAUGE, scale: 0.001}
```

--------

## 自定义采集器

### 创建自己的指标

1. 在默认配置的基础上增加指标时，先将完整配置复制到新目录：

```bash
sudo install -d -m 0755 /etc/pg_exporter
sudo cp -p /etc/pg_exporter.yml /etc/pg_exporter/0000-base.yml
```

已有配置目录时，直接在那里添加新文件。下面将应用采集器保存为 `/etc/pg_exporter/9990-app.yml`，假定应用表已经存在，且 `processing_time` 为以秒计的数值：

```yaml
# /etc/pg_exporter/9990-app.yml
app_metrics:
  desc: "应用特定指标"
  tags: ["dbname:app"]
  query: |
    SELECT
      (SELECT count(*) FROM users WHERE active = true) as active_users,
      (SELECT count(*) FROM orders WHERE created_at > NOW() - '1 hour'::interval) as recent_orders,
      (SELECT avg(processing_time) FROM jobs WHERE completed_at > NOW() - '5 minutes'::interval) as avg_job_time
  ttl: 30
  metrics:
    - active_users: {usage: GAUGE, description: "当前活跃用户数"}
    - recent_orders: {usage: GAUGE, description: "最近一小时的订单数"}
    - avg_job_time: {usage: GAUGE, description: "平均作业处理时间"}
```

2. 将 `PG_EXPORTER_URL` 中的数据库名改为 `app`，保留连接凭据。校验定义并选择采集器：

```bash
pg_exporter --dry-run --config=/etc/pg_exporter/
pg_exporter --explain --fail-fast --config=/etc/pg_exporter/
```

3. 用相同 URL 和配置运行 exporter，在另一个终端请求 `/metrics` 并检查 `/stat`。
   `--explain` 只选择采集器，不执行其 SQL。

软件包服务首次切换到此目录时，将 `/etc/default/pg_exporter` 中的 `PG_EXPORTER_CONFIG` 改为 `/etc/pg_exporter`，再重启服务。之后修改目录中的 YAML 文件，可用 `POST /reload` 重载。

### 条件指标

使用谓词查询实现条件指标：

```yaml
partition_metrics:
  desc: "分区表指标"
  predicate_queries:
    - name: "检查是否使用了分区"
      predicate_query: |
        SELECT EXISTS (
          SELECT 1 FROM pg_class
          WHERE relkind = 'p' LIMIT 1
        )
  query: |
    SELECT
      current_database() AS datname,
      ns.nspname AS schemaname,
      parent.relname AS parent_table,
      count(*) as partition_count,
      sum(pg_relation_size(child.oid)) as total_size
    FROM pg_inherits
    JOIN pg_class parent ON parent.oid = pg_inherits.inhparent
    JOIN pg_class child ON child.oid = pg_inherits.inhrelid
    JOIN pg_namespace ns ON ns.oid = parent.relnamespace
    WHERE parent.relkind = 'p'
    GROUP BY ns.nspname, parent.relname
  ttl: 300
  min_version: 100000
  metrics:
    - datname: {usage: LABEL}
    - schemaname: {usage: LABEL}
    - parent_table: {usage: LABEL}
    - partition_count: {usage: GAUGE}
    - total_size: {usage: GAUGE}
```

--------

## 性能优化

用监控角色测量 SQL 耗时。为高开销采集器设置较长的 TTL，并给正常执行留足超时时间。不需要的采集器可设置 `skip: true`。实例级 SQL 加上 `tags: [cluster]`，避免被自动发现的数据库重复执行。

控制标签取值数量，同时保留能唯一标识结果行的列。例如，跨数据库采集表指标时，表名还需要配合数据库和模式名。不需要对象级序列时，优先在 SQL 中汇总。

### 监控采集器性能

检查采集器执行统计：

```bash
# 查看采集器统计（命中/错误/跳过计数与耗时）
curl http://localhost:9630/stat

# 按 datname/query 维度查看每个采集器的耗时与错误
curl -s http://localhost:9630/metrics | grep -E 'pg_exporter_query_scrape_(duration|error_count)'
```

--------

## 配置故障排查

### 验证配置

```bash
# 干运行 - 显示解析后的配置
pg_exporter --dry-run

# 解释 - 显示计划的查询
pg_exporter --explain
```

### 常见问题

| 问题    | 解决方案               |
|-------|--------------------|
| 指标缺失  | 检查标签和版本兼容性         |
| 抓取缓慢  | 增加 TTL、添加超时、禁用昂贵查询 |
| 内存使用高 | 汇总结果或筛选明确的对象集合   |
| 权限错误  | 验证监控用户的查询权限        |
{.full-width}

### 调试日志

启用调试日志进行故障排查：

```bash
pg_exporter --log.level=debug
```
