---
title: "安全指南"
linkTitle: "安全指南"
description: "数据库最小权限、密钥处理、TLS、HTTP 认证与网络暴露面"
weight: 60
icon: fa-solid fa-shield-halved
categories: [指南]
---

`pg_exporter` 位于两个信任域之间：它先向 PostgreSQL 或 pgBouncer 认证，再通过 HTTP 暴露指标与管理端点。两侧必须独立加固；数据库 TLS 不会保护 HTTP 监听端口，HTTP Basic Auth 也不会降低数据库权限。

## 威胁面

| 表面 | 敏感能力 | 主要控制 |
|:---|:---|:---|
| PostgreSQL 连接 | 读取监控视图并执行采集器 SQL | 专用登录角色、`pg_monitor`、`pg_hba.conf`、TLS |
| 目标 URL | 包含主机、用户，通常还包含密码 | `.pgpass`、密钥文件、文件权限、密钥管理系统 |
| `/metrics` | 暴露拓扑、对象名、负载与容量 | 私网、防火墙、TLS/认证 |
| `/explain` 与 `/stat` | 暴露采集器定义、准入、耗时与错误 | 限制或认证 HTTP 访问 |
| `/reload` | 触发配置解析与查询计划原子替换 | 限制或认证 HTTP 访问 |
| 采集器 SQL | 消耗数据库资源，并可能通过 Label 暴露信息 | 查询审查、最小权限、超时、TTL、基数审查 |
{.full-width}

## 使用专用数据库角色

PostgreSQL 10+ 内置的 `pg_monitor` 角色覆盖默认采集器所需的只读权限：

```sql
CREATE ROLE monitor
  WITH LOGIN
       PASSWORD 'replace-this-secret'
       CONNECTION LIMIT 5;

GRANT pg_monitor TO monitor;
```

不要为了省去权限审查而让 exporter 使用超级用户。可选自定义采集器可能需要访问自己的视图、函数或 Schema，请按对象单独授权。

监控 pgBouncer 时，需要使用本地策略允许的 `stats_users` 或 `admin_users` 账户连接管理数据库。此模式下 exporter 使用管理端 `SHOW` 接口，而不是 PostgreSQL 系统目录。

## 不要把密码放进进程参数

目标 URL 的取值优先级如下：

1. `--url` / `-u`
2. `PG_EXPORTER_URL`
3. `PGURL`
4. `PG_EXPORTER_URL_FILE` 指向的文件
5. `postgresql:///?sslmode=disable`

命令参数可能出现在进程列表中，建议使用以下方式之一。

### `.pgpass`

```text
db.example.com:5432:*:monitor:replace-this-secret
```

```bash
chmod 600 ~/.pgpass
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full'
```

RPM/DEB 服务以 `prometheus` 用户运行。自 v1.4.0 起该用户 HOME 为 `/var/lib/prometheus`，但软件包不会创建目录：

```bash
sudo install -d -o prometheus -g prometheus -m 0750 /var/lib/prometheus
sudo install -o prometheus -g prometheus -m 0600 ./pgpass /var/lib/prometheus/.pgpass
```

### 密钥文件

`PG_EXPORTER_URL_FILE` 适合 systemd credential、Docker/Kubernetes Secret 挂载以及其他文件型密钥交付：

```bash
export PG_EXPORTER_URL_FILE=/run/secrets/pg_exporter_url
pg_exporter --config=/etc/pg_exporter.yml
```

文件应包含一个 URL，可以带首尾空白。显式配置的文件不存在或不可读时，进程会致命退出。日志会遮盖 URL 用户信息与 `password=` 查询参数中的密码，但日志脱敏不能替代源密钥保护。

## 保护数据库连接

未提供 `sslmode` 时，pg_exporter 会为常见的同机部署主动添加 `sslmode=disable`。这在不可信网络上并不安全；远程目标应显式选择 libpq TLS 策略：

```bash
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pg_exporter/ca.crt'
```

尽可能使用 `verify-full`，同时验证证书链与主机名。`require` 会加密流量，但不能提供同等的服务器身份保证。

官方 Docker 镜像基于 `scratch`，没有系统 CA 包。请将所需 CA 文件挂载进容器，并在 `sslrootcert` 中引用精确路径。

## 缩小 HTTP 暴露面

如果 Prometheus 与 exporter 在同一台主机上，只监听回环地址：

```bash
pg_exporter --web.listen-address=127.0.0.1:9630
```

需要远程抓取时，只允许监控网段通过防火墙或服务网格访问。监听端口同时包含管理端点，并不存在独立的管理端口。

### TLS 与 Basic Auth

`--web.config.file` 使用 Prometheus exporter-toolkit 格式，并在每个 HTTP 请求时重新读取。最小示例：

```yaml
tls_server_config:
  cert_file: /etc/pg_exporter/web.crt
  key_file: /etc/pg_exporter/web.key
  min_version: TLS12

basic_auth_users:
  prometheus: "$2y$10$replace_with_a_bcrypt_hash"
```

```bash
pg_exporter --web.config.file=/etc/pg_exporter/web.yml
```

请生成 bcrypt 哈希，不要把明文密码写进文件，例如使用 `htpasswd -nBC 10 prometheus`。mTLS、响应头与限流配置以 [exporter-toolkit Web 配置](https://github.com/prometheus/exporter-toolkit/blob/master/docs/web-configuration.md)为准。

启用 Basic Auth 后，Prometheus 抓取任务也要配置认证：

```yaml
scrape_configs:
  - job_name: postgresql
    scheme: https
    basic_auth:
      username: prometheus
      password_file: /etc/prometheus/secrets/pg_exporter_password
    tls_config:
      ca_file: /etc/prometheus/ca/pg_exporter-ca.crt
    static_configs:
      - targets: ['db.example.com:9630']
```

## 保护配置文件

发布软件包以较严格的权限将 `/etc/pg_exporter.yml` 与 `/etc/default/pg_exporter` 交给 `prometheus` 用户。复制或模板化文件时应保留相同的所有权与权限。数据库密码不应放在采集器 YAML 中；该文件用于查询和指标元数据，不是连接密钥。

部署前还要审查自定义 Label。数据库名、客户标识、租户名与 SQL 指纹都可能成为 Prometheus 标签，并继续流向远端存储、告警与仪表盘。

## 生产检查清单

- 使用有小连接上限的专用非超级用户数据库账户
- 配置明确的 `pg_hba.conf` 规则与网络来源限制
- 使用 `.pgpass` 或密钥文件，不在命令参数中放密码
- 远程数据库连接使用 `sslmode=verify-full` 与可信 CA
- 9630 端口只监听回环/私网，或受防火墙限制
- HTTP 跨越信任边界时启用 TLS/认证
- 将管理端点视为敏感接口
- 审查自定义 SQL 的权限、超时、TTL 与标签基数
- 验证密钥/证书轮换不会在日志或进程列表泄露值

服务示例参见[生产部署](/zh/deploy/)，TLS、凭据与端点失败的定位方法参见[故障排查](/zh/troubleshooting/)。
