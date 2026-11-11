---
title: "HTTP API"
linkTitle: "HTTP API"
description: "指标、健康检查、角色路由、重载、解释、统计与版本端点"
weight: 110
icon: fa-solid fa-plug
categories: [参考]
---

`pg_exporter` 默认在 `:9630` 提供指标、健康检查和管理端点。本页适用于稳定版 **v{{< param version >}}**。用 `--web.listen-address` 设置监听地址，详见[命令参考](/zh/cmd/)。

| 端点 | 方法 | 结果 |
|:---|:---|:---|
| [`/metrics`](#get-metrics) | GET | Prometheus 指标；用 `--web.telemetry-path` 修改路径 |
| [`/up`](#health-checks) | GET、HEAD | 主连接目标的可用状态；别名 `/health`、`/liveness`、`/readiness`、`/read` |
| [`/primary`](#traffic-routing) | GET、HEAD | 主库角色；别名 `/leader`、`/master`、`/read-write`、`/rw` |
| [`/replica`](#traffic-routing) | GET、HEAD | 从库角色；别名 `/standby`、`/slave`、`/read-only`、`/ro` |
| [`/reload`](#operational-endpoints) | GET、POST | 重载采集器配置 |
| [`/explain`](#get-explain) | GET | 主连接选中的采集器的纯文本说明 |
| [`/stat`](#get-stat) | GET | 主连接采集器运行统计，纯文本格式 |
| [`/version`](#get-version) | GET | 版本与构建信息，纯文本格式 |
| `/` | GET | 含指标链接的 HTML 页面 |
{.full-width}

表中列出各端点的常用方法，只有 `/reload` 会明确拒绝其他方法。未匹配路径会交给根页面处理，配置探针时请使用表中的路径。

## 指标端点 {#metrics-endpoint}

### GET /metrics {#get-metrics}

每次请求都会采集主目标及自动发现数据库的指标。采集器缓存有效时，直接返回缓存结果。

```bash
curl -fsS http://127.0.0.1:9630/metrics
```

响应示例：

```prometheus
# HELP pg_up last scrape was able to connect to the server: 1 for yes, 0 for no
# TYPE pg_up gauge
pg_up 1
# HELP pg_version server version number
# TYPE pg_version gauge
pg_version 180000
# HELP pg_in_recovery server is in recovery mode? 1 for yes 0 for no
# TYPE pg_in_recovery gauge
pg_in_recovery 0
```

数据库故障时，端点仍可能返回 HTTP 200，正文中 `pg_up` 为 0。检查 HTTP 状态时也要检查指标。普通采集器出错后，本轮不输出该采集器的结果，其他采集器继续执行。致命采集器出错后，停止该数据库的后续采集。HTTP 500 表示指标汇总或编码失败，例如指标定义冲突。

自 v1.6.0 起，采集、等待与响应写入阶段合计最多接纳两个指标请求。采集仍串行；第二个请求在剩余预算内等待，更多请求返回 HTTP 503。预算默认为 30 秒，合法、有限且为正数的 `X-Prometheus-Scrape-Timeout-Seconds` 请求头可以缩短它。等待期间取消的请求不执行 SQL。

请求取消后，不再启动下一个采集器或数据库。已启动且 timeout 为正数的采集器，其谓词链与主 SQL 共用同一期限，继续执行并正常缓存结果。负数 timeout 关闭该期限，此时查询随请求取消。中断的采集在连接仍允许响应时返回 503。驱动与网络阻塞意味着这些期限不是硬性的墙钟上限；建连握手需另行设置 DSN 的 `connect_timeout`。

中断轮次不增加 `pg_exporter_scrape_error_count` 和 `pg_exporter_server_scrape_error_count`，轮次汇总日志为 INFO `interrupted`；查询错误计数与 fatal 查询的 ERROR 日志仍然保留。因此，恰好与请求取消重叠的真实失败可能不计入这两个轮次计数。请求没有取消时，连接／预检失败和 fatal 查询失败（包括自身超时）仍按错误计数；非 fatal 失败仍体现在查询级计数中。

刷新失败沿用原有失败 TTL。尤其是负数 timeout 的 fatal 采集器，被取消后会缓存 fatal 失败；后续有效抓取可能对该失败计数并返回 `pg_up 0`，直到成功刷新。建议 fatal 采集器保留正数 timeout。设计理由见 [采集生命周期](/zh/design/scrape-lifetime/)。

### 自监控指标 {#self-monitoring-metrics}

PostgreSQL 的内置指标前缀默认为 `pg`，PgBouncer 默认为 `pgbouncer`。`--namespace` 可以修改此类前缀，非法前缀会在启动时被拒绝；它不会改变 YAML 中定义的指标名。

| 指标 | 类型 | 标签 | 含义 |
|:---|:---|:---|:---|
| `pg_up` | Gauge | — | 采集所见的主目标可用状态；中断规则见下文 |
| `pg_version` | Gauge | — | 主目标的版本号 |
| `pg_in_recovery` | Gauge | — | 从库为 1，主库为 0；在 `pg_up = 1` 时使用 |
| `pg_exporter_build_info` | Gauge | version、revision、branch、builddate、goversion、goos、goarch | 恒为 1，标签记录构建信息 |
| `pg_exporter_up` | Gauge | — | 恒为 1 |
| `pg_exporter_uptime` | Gauge | — | exporter 初始化以来的秒数 |
| `pg_exporter_scrape_total_count` | Counter | — | 采集轮数 |
| `pg_exporter_scrape_error_count` | Counter | — | 主目标出现连接错误或致命采集器错误的轮数 |
| `pg_exporter_scrape_duration` | Gauge | — | 最近一轮完整采集的耗时，单位秒 |
| `pg_exporter_last_scrape_time` | Gauge | — | 最近一轮采集结束时的 Unix 时间戳 |
| `pg_exporter_server_scrape_duration` | Gauge | datname | 数据库最近一轮采集的耗时，单位秒 |
| `pg_exporter_server_scrape_total_seconds` | Gauge | datname | 数据库累计采集耗时，单位秒 |
| `pg_exporter_server_scrape_total_count` | Gauge | datname | 数据库采集轮数 |
| `pg_exporter_server_scrape_error_count` | Gauge | datname | 数据库连接错误或致命采集器错误次数 |
| `pg_exporter_query_scrape_total_count` | Gauge | datname、query | 采集器调用次数，含缓存命中和谓词跳过 |
| `pg_exporter_query_scrape_error_count` | Gauge | datname、query | 采集器调用报错次数 |
| `pg_exporter_query_scrape_hit_count` | Gauge | datname、query | 结果缓存命中次数 |
| `pg_exporter_query_scrape_metric_count` | Gauge | datname、query | 采集器当前结果中的样本数 |
| `pg_exporter_query_scrape_duration` | Gauge | datname、query | 最近一次实际执行耗时，单位秒；缓存命中时保留原值 |
| `pg_exporter_query_scrape_predicate_skip_count` | Gauge | datname、query | 谓词返回 false、NULL 或零行而跳过的次数 |
| `pg_exporter_query_cache_ttl` | Gauge | datname、query | 结果缓存剩余有效期，单位秒 |
{.full-width .wide .expand}

这些序列也会附加配置的固定标签。在 `pg_exporter_build_info` 上，`version`、`revision`、`branch`、`builddate`、`goversion`、`goos` 与 `goarch` 的构建信息值优先于用户标签。数据库或查询级内置样本的标签无效时，会记录警告并跳过该样本，避免 panic。数据库和采集器级别的累计计数以 Gauge 暴露。服务器重新规划时会重置采集器统计，配置重载也会触发这一过程。数据库连接对象重建时会重置该数据库的统计。

`--disable-intro` 会隐藏表中所有内置指标，包括 `pg_up`。YAML 指标、Go/进程指标和 HTTP 健康检查仍然可用。

中断时，`pg_up` 保留主目标此前的可用状态；若本轮预检已成功，则保留为 1。首次预检在成功前被中断时，保持为 0，后续成功抓取可恢复。子数据库中断采用相同的单库规则，不增加主目标的错误计数。

## 健康检查 {#health-checks}

### GET /up {#get-up}

初始化后，HTTP 健康状态只由每秒一次的后台探测更新。慢采集不再占用探测所需的锁，采集完成也不会覆盖更新的探测结果。HTTP 健康请求只读取快照，不执行 SQL。`pg_up` 与 `pg_in_recovery` 仍属于采集指标：fatal 采集器失败可能使 `pg_up` 为 0，而数据库可达时 `/up` 仍返回 200。PostgreSQL 主连接池最多三个连接，PgBouncer 最多两个，每个发现数据库最多一个。

| 响应正文 | HTTP 状态 | 含义 |
|:---|:---|:---|
| `primary` | 200 | 目标可达，且未处于恢复模式 |
| `replica` | 200 | 目标可达，且处于恢复模式 |
| `starting` | 503 | PostgreSQL 在健康探测时返回 SQLSTATE `57P03` |
| `down` | 503 | 目标探测失败 |
| `unknown` | 503 | 尚无健康状态 |

```bash
curl -i http://127.0.0.1:9630/up
```

`/health`、`/liveness`、`/readiness` 和 `/read` 使用同一处理器，检查的是数据库目标，而非 exporter 进程本身。在 Kubernetes 中，如果希望数据库故障只影响就绪状态、不重启 exporter，可使用 TCP 存活探针和 HTTP 就绪探针：

```yaml
livenessProbe:
  tcpSocket: { port: 9630 }
  initialDelaySeconds: 5
  periodSeconds: 10
readinessProbe:
  httpGet: { path: /readiness, port: 9630 }
  initialDelaySeconds: 5
  periodSeconds: 5
```

## 流量路由 {#traffic-routing}

角色检查使用主连接 PostgreSQL 目标的 `pg_is_in_recovery()`。它们判断角色和连通性，不检查应用权限或事务只读设置。

| 缓存状态 | `/primary` | `/replica` | `/read` |
|:---|:---|:---|:---|
| `primary` | 200 | 404 | 200 |
| `replica` | 404 | 200 | 200 |
| `down`、`starting`、`unknown` | 503 | 503 | 503 |

响应正文为状态名称。在 PgBouncer 模式下，`SHOW VERSION` 探测成功会被映射为 `primary`，并不代表连接池后端 PostgreSQL 的角色。按角色路由时，应使用直接连接 PostgreSQL 的 exporter。

每个健康响应从同一个原子状态快照生成 HTTP 状态码与正文，修复并发状态变化时可能出现的矛盾响应；状态仍然来自缓存。指标路径校验还会确认请求在当前 HTTP mux 下确实进入指标处理器。为兼容旧版 mux，优先使用 `/metrics` 这样的未转义路径。

### GET /primary {#get-primary}

别名：`/leader`、`/master`、`/read-write`、`/rw`。

### GET /replica {#get-replica}

别名：`/standby`、`/slave`、`/read-only`、`/ro`。

### GET /read {#get-read}

`/up` 的别名，主库和从库均可返回成功。

### HAProxy 示例 {#haproxy-example}

在每个 PostgreSQL 实例旁运行 exporter。客户端流量发送到 5432 端口，健康检查发送到 9630 端口：

```haproxy
backend pg_primary
  mode tcp
  option httpchk GET /primary
  http-check expect status 200
  server pg1 10.0.0.1:5432 check port 9630 inter 3000 fall 2 rise 2
  server pg2 10.0.0.2:5432 check port 9630 inter 3000 fall 2 rise 2

backend pg_replicas
  mode tcp
  balance roundrobin
  option httpchk GET /replica
  http-check expect status 200
  server pg1 10.0.0.1:5432 check port 9630 inter 3000 fall 2 rise 2
  server pg2 10.0.0.2:5432 check port 9630 inter 3000 fall 2 rise 2
```

将 `/replica` 换为 `/read`，即可让读流量使用任意可用角色。

## 运维端点 {#operational-endpoints}

### GET /reload / POST /reload {#get-reload--post-reload}

用 POST 重载当前选择的配置文件或目录：

```bash
curl -fsS -X POST http://127.0.0.1:9630/reload
```

| HTTP 状态 | 响应 | 含义 |
|:---|:---|:---|
| 200 | `server reloaded` | 新定义已生效，下次抓取时重新规划 |
| 500 | `fail to reload: ...` | 重载被拒绝，继续使用之前的定义 |
| 405 | `method not allowed` | 请用 GET 或 POST；响应头包含 `Allow: GET, POST` |

重载会替换采集器定义，清除其缓存和查询统计，使旧计划失效。重载不会执行新 SQL。空 YAML 文件属于有效配置，会将计划替换为零个配置采集器，内置指标仍保留；单文件重载被拒绝时保留旧定义。完成后抓取 `/metrics`，检查采集器错误。目录加载可以跳过无效文件并加载其他有效文件，应检查日志中的 `skip config` 警告。

Unix 上还可以发送 `SIGHUP` 或 `SIGUSR1` 重载。`SIGTERM` 会结束进程，不等待活跃 HTTP 请求完成。修改连接 URL、固定标签、Tag 或监听地址需要重启进程。通过防火墙、反向代理或 `--web.config.file` 限制管理访问，详见[安全指南](/zh/security/)。

### GET /explain {#get-explain}

返回主连接选中的采集器的纯文本定义，包括 SQL、标签、TTL、超时和指标映射。首次规划前和刚完成重载时，输出为空。先执行一次抓取：

```bash
curl -fsS http://127.0.0.1:9630/metrics >/dev/null
curl -fsS http://127.0.0.1:9630/explain
```

此端点不执行 PostgreSQL `EXPLAIN` 或谓词查询，不列出被排除的分支，也不包含自动发现数据库的计划。分支排除原因见调试日志。查看其他数据库的计划时，用 `pg_exporter --explain --fail-fast --url=...` 直接连接该数据库。

### GET /stat {#get-stat}

返回主连接选中的采集器的纯文本统计表：

```bash
curl -fsS http://127.0.0.1:9630/stat
```

```text
name                     total      hit        error      skip       metric     ttl/s  duration/ms
pg                       12         0          0          0          15         1      4.231000
pg_db                    12         11         0          0          28         0      0.153000
```

`total` 是调用次数，`hit` 是缓存命中次数，`error` 是报错次数，`skip` 是谓词跳过次数。`metric` 是当前样本数，`ttl/s` 是取整后的剩余缓存秒数，`duration/ms` 是最近一次实际执行耗时。比较所有自动发现数据库时，使用 `pg_exporter_query_*` 指标。

### GET /version {#get-version}

返回版本、提交、分支、Go 版本、构建日期、操作系统和架构：

```bash
curl -fsS http://127.0.0.1:9630/version
```

验证部署时，用此端点确认正在运行的二进制版本。
