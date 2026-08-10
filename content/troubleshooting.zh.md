---
title: "故障排查"
linkTitle: "故障排查"
description: "按症状定位启动、连接、指标缺失、慢抓取、重载与软件包问题"
weight: 70
icon: fa-solid fa-stethoscope
categories: [指南]
---

首先把问题拆成四层：进程、HTTP、数据库连接、单个采集器。systemd 单元运行只证明进程层；`pg_up 1` 证明当前目标连接与致命采集器路径；Prometheus 成功抓取才证明端到端 HTTP 路径。

## 五分钟分诊

```bash
# 进程与日志
systemctl status pg_exporter --no-pager
journalctl -u pg_exporter -n 100 --no-pager

# HTTP 与构建身份
curl -fsS http://127.0.0.1:9630/version
curl -i http://127.0.0.1:9630/up

# 核心指标
curl -fsS http://127.0.0.1:9630/metrics \
  | grep -E '^(pg|pgbouncer)_(up|version|in_recovery) '

# 规划与运行证据
curl -fsS http://127.0.0.1:9630/explain
curl -fsS http://127.0.0.1:9630/stat
```

| 现象 | 优先检查的层面 |
|:---|:---|
| 单元立即退出 | 参数、配置路径、指标路径、监听地址、文件权限 |
| 端口可访问但 `/up` 为 503 | 目标 URL、网络、认证、`pg_hba.conf`、TLS、启动探测状态 |
| `/up` 为 200，但某指标族缺失 | 动态规划、版本/角色/标签/谓词、自动发现、关闭的采集器 |
| `/metrics` 报错或 Prometheus 超时 | 致命采集器、慢查询、抓取超时、Label/Schema 不匹配 |
| exporter 健康但 Prometheus Target Down | Prometheus 地址、协议、认证、TLS、防火墙、指标路径 |
{.full-width}

## 进程无法启动

### `no valid config path`

配置搜索顺序为 `--config`、`PG_EXPORTER_CONFIG`、`./pg_exporter.yml`、`/etc/pg_exporter.yml`、`/etc/pg_exporter`。确认运行用户可以读取文件：

```bash
sudo -u prometheus test -r /etc/pg_exporter.yml
sudo -u prometheus /usr/bin/pg_exporter \
  --config=/etc/pg_exporter.yml \
  --dry-run >/dev/null
```

`--dry-run` 不需要在线数据库，会解析并解释原始配置。配置目录不递归，只按字母顺序加载 `.yaml` / `.yml`；后加载文件中的同名顶层分支会覆盖前一个定义。

### 指标路径非法

自 v1.4.0 起，`--web.telemetry-path` 必须是以 `/` 开头的规范字面路径，不能包含查询串、Fragment、Go ServeMux 通配符，也不能与 `/up`、`/reload`、`/version` 等内置端点冲突。

没有明确需求时保持 `/metrics`，修改后还要同步调整 Prometheus 的 `metrics_path`。

### 地址已被占用

```bash
lsof -nP -iTCP:9630 -sTCP:LISTEN
```

停止冲突服务或更换 `--web.listen-address`。不要让两个 exporter 竞争同一地址并假设其中一个会正常工作。

## `pg_up` 为 0 或 `/up` 返回 503

临时使用调试日志与脱敏后的显式 URL 启动：

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

软件包服务以 `prometheus` 用户运行；用当前 Shell 用户测试成功，并不能证明服务用户也能成功。

非阻塞启动是正常行为：目标不可用时 HTTP 服务器仍会运行，后台探测继续重试。只有希望编排系统将初始数据库不可达视为进程启动失败时，才使用 `--fail-fast`。

## 指标缺失

缺失通常来自规划决策，而不是抓取 Bug。查看 `/explain`，重点寻找：

- 服务器版本不在 `[min_version, max_version)`；
- 主库/从库角色不匹配；
- `extension:`、`schema:`、`dbname:` 或 `username:` 事实缺失；
- 自定义正标签缺失，或命中了 `not:` 标签；
- 谓词查询返回 false；
- `skip: true`；
- 数据库被自动发现排除。

启用自动发现时，默认排除 `template0,template1,postgres`。如果预期来自 `postgres` 的指标缺失，应有意识地调整 `PG_EXPORTER_EXCLUDE_DATABASE`，不要假设所有数据库都会抓取。

## 单个采集器失败

通过 `/stat` 与 exporter 自监控指标定位精确的采集器和数据库：

```promql
pg_exporter_query_scrape_error_count > 0
```

常见原因：

- 监控角色无权访问可选视图或函数；
- 扩展/Schema 安装在另一个数据库；
- 自定义 SQL 结果列与 YAML `metrics` 清单不一致；
- 配置声明的 `LABEL` 列没有返回（v1.4.1 会原子拒绝整个采集器结果）；
- 查询超过超时；
- 扩展或预发布 PostgreSQL 视图结构变化。

请在相同数据库中以监控用户手工执行采集器 SQL，并确保即使返回零行，结果列名也完整一致。

## 抓取缓慢或超时

`/stat` 会报告逐采集器最后耗时与错误；Prometheus 自监控指标按 `datname` 与查询名提供相同证据。

常见处理顺序：

1. 优化或缩小 SQL 范围。
2. 增加 `ttl`，让昂贵结果在多次抓取之间复用。
3. 将合理的逐查询 `timeout` 设置在 Prometheus 抓取超时以内。
4. 用 `skip: true` 关闭可选高开销采集器。
5. 通过 `include-database` / `exclude-database` 缩小自动发现范围。
6. 控制拥有数千张表/索引数据库上的逐对象指标基数。

不要只把 Prometheus `scrape_timeout` 调大到足以掩盖无边界查询。完整抓取应明显短于超时与抓取间隔。

## 重载失败

```bash
curl -i -X POST http://127.0.0.1:9630/reload
```

- `200`：新查询集已完成解析、校验、安装，现有计划已失效并将在下次抓取重建。
- `500`：响应包含解析、Schema、Label 冲突或配置路径错误；旧活动查询集仍然保留。
- `405`：只能使用 GET 或 POST，推荐 POST。

进程级选项不能热重载。监听地址、目标 URL、日志、HTTP TLS/认证、命名空间或发现参数变化需要重启服务。采集器 YAML 也可以通过 `SIGHUP` 重载；Unix 构建还支持 `SIGUSR1`。

## Docker 与软件包常见坑

| 现象 | 可能原因与修复 |
|:---|:---|
| Docker 中 TLS 校验失败 | `scratch` 镜像没有 CA 包；挂载 CA 并设置 `sslrootcert` |
| 软件包服务忽略 `.pgpass` | 创建 `/var/lib/prometheus`，归属 `prometheus`，`.pgpass` 使用 `0600` |
| RPM 自动化找不到 v1.4.1 产物 | 产物前缀从 `pg_exporter` 改为 `pg-exporter` |
| 容器替换后配置修改消失 | 将 `/etc/pg_exporter.yml` 从持久配置挂载 |
| 容器无法访问宿主机 PostgreSQL | `localhost` 指容器自身；使用数据库服务 DNS 或明确的宿主机路由 |
{.full-width}

## Bug 报告应包含的证据

- `pg_exporter /version` 输出与安装方式
- 操作系统与体系结构
- PostgreSQL 或 PgBouncer 精确版本
- 脱敏目标 URL（保留协议、主机类别、端口、数据库与 `sslmode`）
- 相关采集器 YAML 与 SQL，并移除密钥
- 故障附近的 Debug 日志
- 该采集器对应的 `/explain` 与 `/stat` 内容
- 使用 v{{< param version >}} 内置配置是否可以复现

移除密码、证书、客户标识与敏感 SQL 后，再到 [pgsty/pg_exporter Issues](https://github.com/pgsty/pg_exporter/issues) 提交问题。
