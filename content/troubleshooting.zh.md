---
title: "故障排查"
linkTitle: "故障排查"
description: "按症状定位启动、连接、指标缺失、慢抓取、重载与软件包问题"
weight: 70
icon: fa-solid fa-stethoscope
categories: [指南]
---

按进程、HTTP 访问、数据库连接、单个采集器的顺序检查。`pg_up 1` 表示上次抓取成功连接主目标，并完成了标记为 `fatal` 的采集器；其他采集器或自动发现库仍可能出错。

## 初步检查 {#initial-checks}

```bash
# 进程与日志
systemctl status pg_exporter --no-pager
journalctl -u pg_exporter -n 100 --no-pager

# HTTP 响应与版本
curl -fsS http://127.0.0.1:9630/version
curl -i http://127.0.0.1:9630/up

# 核心指标
curl -fsS http://127.0.0.1:9630/metrics \
  | grep -E '^(pg|pgbouncer)_(up|version|in_recovery)(\{| )'

# 采集计划与运行统计
curl -fsS http://127.0.0.1:9630/explain
curl -fsS http://127.0.0.1:9630/stat
```

| 现象 | 优先检查的层面 |
|:---|:---|
| 单元立即退出 | 参数、配置路径、指标路径、监听地址、文件权限 |
| 端口可访问但 `/up` 为 503 | 目标 URL、网络、认证、`pg_hba.conf`、TLS、启动探测状态 |
| `/up` 为 200，但某指标族缺失 | 动态规划、版本/角色/标签/谓词、自动发现、关闭的采集器 |
| `/metrics` 报错或 Prometheus 超时 | 慢查询、抓取超时、重复或无效的指标样本 |
| exporter 健康但 Prometheus Target Down | Prometheus 地址、协议、认证、TLS、防火墙、指标路径 |
{.full-width}

## 进程无法启动 {#process-will-not-start}

### `no valid config path` {#no-valid-config-path}

配置搜索顺序为 `--config`、`PG_EXPORTER_CONFIG`、`./pg_exporter.yml`、`/etc/pg_exporter.yml`、`/etc/pg_exporter`。确认运行用户可以读取文件：

```bash
sudo -u prometheus test -r /etc/pg_exporter.yml
sudo -u prometheus /usr/bin/pg_exporter \
  --config=/etc/pg_exporter.yml \
  --dry-run >/dev/null
```

`--dry-run` 不需要在线数据库，会解析并解释原始配置。配置目录不递归，只按字母顺序加载 `.yaml` / `.yml`；后加载文件中的同名顶层分支会覆盖前一个定义。

### 指标路径非法 {#invalid-telemetry-path}

自 v1.4.0 起，`--web.telemetry-path` 必须是以 `/` 开头的规范字面路径，不能包含查询串、Fragment、Go ServeMux 通配符，也不能与 `/up`、`/reload`、`/version` 等内置端点冲突。

没有明确需求时保持 `/metrics`，修改后还要同步调整 Prometheus 的 `metrics_path`。

### 地址已被占用 {#address-already-in-use}

```bash
lsof -nP -iTCP:9630 -sTCP:LISTEN
```

停止冲突服务或更换 `--web.listen-address`。

## `pg_up` 为 0 或 `/up` 返回 503 {#pg_up-is-0-or-up-returns-503}

软件包服务可在 `/etc/default/pg_exporter` 的 `PG_EXPORTER_OPTS` 中设置 `--log.level=debug`，再重启服务。这样会保留原来的运行用户与连接设置：

```bash
sudo systemctl restart pg_exporter
sudo journalctl -u pg_exporter -f
```

前台运行时，使用实际目标 URL，通过 `.pgpass` 或密钥文件提供密码：

```bash
PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pg_exporter/ca.crt' \
pg_exporter --config=/etc/pg_exporter.yml --log.level=debug
```

依次检查：

1. DNS 与目标主机端口的 TCP 可达性。
2. 数据库名与登录角色。
3. `pg_hba.conf` 的来源地址、认证方式与重载状态。
4. 密码来源：URL、`.pgpass` 或 `PG_EXPORTER_URL_FILE`。
5. `.pgpass` 是否为 `0600`、主机名是否匹配、运行用户 HOME 是否正确。
6. TLS CA 路径、主机名与 `sslmode`。
7. 监控角色连接上限与服务器总连接耗尽。
8. `--connect-timeout`：连接与元数据探测默认超时为 100 毫秒；正常网络延迟超过此预算时，应提高该值。

排查后恢复 `--log.level=info` 并重启服务。

软件包服务以 `prometheus` 用户运行；用当前 Shell 用户测试成功，并不能证明服务用户也能成功。

非阻塞启动是正常行为：目标不可用时 HTTP 服务器仍会运行，后台探测继续重试。只有希望编排系统将初始数据库不可达视为进程启动失败时，才使用 `--fail-fast`。

## 指标缺失 {#metrics-are-missing}

先抓取一次 `/metrics` 以生成计划。`/explain` 只显示主目标上选中的采集器。采集器缺失时，对照 YAML 检查服务器版本、角色与标签；调试日志会记录分支未被选中的原因。重点检查：

- 服务器版本不在 `[min_version, max_version)`；
- 主库/从库角色不匹配；
- `extension:`、`schema:`、`dbname:` 或 `username:` 事实缺失；
- 自定义正标签缺失，或命中了 `not:` 标签；
- 谓词查询返回 false；
- `skip: true`；
- 数据库被自动发现排除。

包含/排除名单只影响额外发现的数据库。连接 URL 指定的数据库始终会被监控，即使它在默认排除名单 `template0,template1,postgres` 中。选中的采集器也可能被谓词跳过，或者查询成功但返回零行；结合 `/stat` 与 SQL 结果检查。

## 单个采集器失败 {#one-collector-fails}

通过 `/stat` 检查主目标。全部监控库的采集器状态由带 `datname`、`query` 标签的自监控指标提供：

```promql
pg_exporter_query_scrape_error_count > 0
```

该值统计自上次生成计划以来的错误，非零值可能来自历史故障。再次抓取，检查数值是否增长，并从日志读取错误内容。

常见原因：

- 监控角色无权访问可选视图或函数；
- 扩展/Schema 安装在另一个数据库；
- 自定义 SQL 结果列与 YAML `metrics` 清单不一致；
- 配置声明的 `LABEL` 列没有返回（本次不会输出该采集器的任何指标）；
- 查询超过超时；
- 扩展或预发布 PostgreSQL 视图结构变化。

请在相同数据库中以监控用户手工执行采集器 SQL，并确保即使返回零行，结果列名也完整一致。

## 抓取缓慢或超时 {#scrapes-are-slow-or-time-out}

自 v1.6.0 起，采集、等待与响应写入阶段合计最多接纳两个指标请求。采集仍串行；第二个请求在剩余预算内等待，更多请求返回 HTTP 503。预算默认为 30 秒，合法、有限且为正数的 `X-Prometheus-Scrape-Timeout-Seconds` 请求头可以缩短它。等待期间取消的请求不执行 SQL。

请求取消后，不再启动下一个采集器或数据库。已启动且 timeout 为正数的采集器，其谓词链与主 SQL 共用同一期限，继续执行并正常缓存结果。负数 timeout 关闭该期限，此时查询随请求取消。中断的采集在连接仍允许响应时返回 503。驱动与网络阻塞意味着这些期限不是硬性的墙钟上限；建连握手需另行设置 DSN 的 `connect_timeout`。

中断轮次不增加 `pg_exporter_scrape_error_count` 和 `pg_exporter_server_scrape_error_count`，轮次汇总日志为 INFO `interrupted`；查询错误计数与 fatal 查询的 ERROR 日志仍然保留。因此，恰好与请求取消重叠的真实失败可能不计入这两个轮次计数。请求没有取消时，连接／预检失败和 fatal 查询失败（包括自身超时）仍按错误计数；非 fatal 失败仍体现在查询级计数中。

刷新失败沿用原有失败 TTL。尤其是负数 timeout 的 fatal 采集器，被取消后会缓存 fatal 失败；后续有效抓取可能对该失败计数并返回 `pg_up 0`，直到成功刷新。建议 fatal 采集器保留正数 timeout。设计理由见 [采集生命周期](/zh/design/scrape-lifetime/)。

`/stat` 以毫秒显示主目标各查询的耗时；`pg_exporter_query_scrape_duration` 按 `datname`、`query` 标签以秒报告耗时。两者都提供错误次数，具体错误内容在日志中。

常见处理顺序：

1. 优化或缩小 SQL 范围。
2. 增加 `ttl`，让昂贵结果在多次抓取之间复用。
3. 将合理的逐查询 `timeout` 设置在 Prometheus 抓取超时以内。
4. 用 `skip: true` 关闭可选高开销采集器。
5. 通过 `include-database` / `exclude-database` 缩小自动发现范围。
6. 控制拥有数千张表/索引数据库上的逐对象指标基数。

查询与自动发现库按顺序抓取，需要为总耗时留出预算。完整抓取应短于 Prometheus 的 `scrape_timeout` 与 `scrape_interval`；HTTP 服务另有 30 秒写超时。

## 重载失败 {#reload-fails}

```bash
curl -i -X POST http://127.0.0.1:9630/reload
```

- `200`：新配置已加载并通过校验，下次抓取将重新生成采集计划。
- `500`：响应包含解析、Schema、Label 冲突或配置路径错误；旧活动查询集仍然保留。
- `405`：只能使用 GET 或 POST，推荐 POST。

目标 URL、监听地址、日志、命名空间、发现参数或 `--web.config.file` 路径改变后，需要重启服务。exporter-toolkit 会动态读取 Web 配置文件内容；同一路径下更新证书或 Basic Auth 设置不使用 `/reload`。

采集器 YAML 也可以通过 `SIGHUP` 重载；Unix 构建还支持 `SIGUSR1`。重载后，下次抓取重建计划，逐查询统计随之清零。

## Docker 与软件包常见坑 {#docker-and-package-pitfalls}

| 现象 | 可能原因与修复 |
|:---|:---|
| Docker 中 TLS 校验失败 | v1.6.0 起包含公共 CA 根证书；检查主机名与信任链，私有 CA 仍需挂载并设置 `sslrootcert` |
| 软件包服务忽略 `.pgpass` | 检查 `prometheus` 的主目录或 `PGPASSFILE`，将文件归属服务用户并设为 `0600` |
| RPM 自动化找不到 v1.4.1 产物 | 产物前缀从 `pg_exporter` 改为 `pg-exporter` |
| 容器替换后配置修改消失 | 将 `/etc/pg_exporter.yml` 从持久配置挂载 |
| 容器无法访问宿主机 PostgreSQL | `localhost` 指容器自身；使用数据库服务 DNS 或明确的宿主机路由 |
{.full-width}

## Bug 报告应包含的证据 {#evidence-to-include-in-a-bug-report}

- `pg_exporter --version` 或 `curl http://127.0.0.1:9630/version` 输出，以及安装方式
- 操作系统与体系结构
- PostgreSQL 或 PgBouncer 精确版本
- 脱敏目标 URL（保留协议、主机类别、端口、数据库与 `sslmode`）
- 相关采集器 YAML 与 SQL，并移除密钥
- 故障附近的 Debug 日志
- 该采集器对应的 `/explain` 与 `/stat` 内容
- 使用 v{{< param version >}} 内置配置是否可以复现

移除密码、私钥、客户标识与敏感 SQL 后，将上述信息提交到 [pgsty/pg_exporter Issues](https://github.com/pgsty/pg_exporter/issues)。
