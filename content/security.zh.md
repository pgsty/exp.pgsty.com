---
title: "安全指南"
linkTitle: "安全指南"
description: "数据库最小权限、密钥处理、TLS、HTTP 认证与网络暴露面"
weight: 60
icon: fa-solid fa-shield-halved
categories: [指南]
---

分别配置数据库访问与 HTTP 访问：用专用监控角色执行 SQL，保护连接凭据，并将 HTTP 端口限制在监控客户端可访问的范围。

## 需要保护的访问 {#access-to-protect}

| 访问入口 | 能力或可见信息 | 控制方式 |
|:---|:---|:---|
| PostgreSQL 连接 | 读取监控视图并执行采集器 SQL | 专用登录角色、`pg_monitor`、`pg_hba.conf`、TLS |
| 目标 URL | 包含主机、用户，通常还包含密码 | `.pgpass`、密钥文件、文件权限、密钥管理系统 |
| `/metrics` | 暴露拓扑、对象名、负载与容量 | 私网、防火墙、TLS/认证 |
| `/explain` 与 `/stat` | 暴露采集器定义、所选分支、耗时与错误 | 限制或认证 HTTP 访问 |
| `/reload` | 重载采集器配置 | 限制或认证 HTTP 访问 |
| 采集器 SQL | 消耗数据库资源，并可能通过 Label 暴露信息 | 查询审查、最小权限、超时、TTL、基数审查 |
{.full-width .wide .expand}

## 使用专用数据库角色 {#use-a-dedicated-database-role}

PostgreSQL 10+ 可先创建登录角色，再授予内置的 `pg_monitor` 角色：

```sql
CREATE ROLE monitor
  WITH LOGIN
       PASSWORD 'replace-this-secret'
       CONNECTION LIMIT 5;

GRANT pg_monitor TO monitor;
```

PostgreSQL 10–13 的 v1.6.0 默认订阅采集器还需要在 Exporter 的 **主连接数据库** 中执行以下列级授权，不能只在订阅所属数据库授权：

```sql
GRANT SELECT (oid) ON pg_catalog.pg_subscription TO monitor;
```

该授权不开放 `subconninfo`。PG14+ 在标准目录 ACL 下无需额外授权，升级约定见[订阅身份与接收器状态](/zh/collectors/#subscription-identity-and-receiver-states)。

如果集群撤销了 `PUBLIC` 的数据库连接权限，为监控角色授予各目标库的 `CONNECT`。可选视图、函数与 Schema 按需授权；exporter 无需超级用户权限。

按监控库数量设置连接上限。主目标连接池最多三个连接，每个额外发现的数据库最多一个。示例中的五个连接适合小规模目标；监控更多数据库或多个 exporter 共用角色时，相应提高上限。

监控 PgBouncer 时，将监控账号加入 `stats_users`，并连接 `pgbouncer` 管理数据库。内置采集器使用 `SHOW` 命令，无需 `admin_users` 权限。

## 不要把密码放进进程参数 {#keep-passwords-out-of-process-arguments}

命令参数可能出现在进程列表中，建议使用以下方式之一。

### `.pgpass` {#pgpass}

先将密码保存到 `./pgpass`：

```bash
umask 077
printf '%s\n' 'db.example.com:5432:*:monitor:replace-this-secret' > ./pgpass
```

前台运行时，将文件安装到当前用户的主目录：

```bash
install -m 0600 ./pgpass ~/.pgpass
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full'
```

RPM/DEB 服务以 `prometheus` 用户运行。软件包为新建账号设置 HOME `/var/lib/prometheus`，已有账号保持原样，目录也不会自动创建。先用 `getent passwd prometheus` 检查主目录，再安装密码文件。使用软件包默认主目录时：

```bash
sudo install -d -o prometheus -g prometheus -m 0750 /var/lib/prometheus
sudo install -o prometheus -g prometheus -m 0600 ./pgpass /var/lib/prometheus/.pgpass
```

### 密钥文件 {#secret-file}

`PG_EXPORTER_URL_FILE` 适合 systemd credential、Docker/Kubernetes Secret 挂载以及其他文件型密钥交付：

```bash
unset PG_EXPORTER_URL PGURL
export PG_EXPORTER_URL_FILE=/run/secrets/pg_exporter_url
pg_exporter --config=/etc/pg_exporter.yml
```

文件必须包含一个连接 URL，且运行用户可读；首尾空白会被移除。选用此来源后，文件不可读会使启动失败。先清除更高优先级的 URL 设置；软件包服务还需删除 `/etc/default/pg_exporter` 中的 `PG_EXPORTER_URL`。

日志会遮盖有效 URL 中的密码与 `password=` 参数，错误 URL 的诊断也不包含原始连接串。源文件仅允许服务账号及其管理员读取。

URL 格式或查询参数转义错误会阻止启动。解码后的查询参数名不能为空，也不能包含 Unicode 空白或 `=`。诊断使用固定文本，不包含连接串或错误参数名。拒绝这些输入可避免显式 TLS 设置在规范化时被静默丢弃。选用 `PG_EXPORTER_URL_FILE` 时，空内容或仅含空白的内容也会被拒绝；这里检查的是连接 URL 文件，不是 TLS 私钥文件。

## 保护数据库连接 {#secure-the-database-connection}

URL 未提供 `sslmode` 时，pg_exporter 会添加 `sslmode=disable`。通过网络连接数据库时，明确设置 TLS 模式与 CA 路径：

```bash
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pg_exporter/ca.crt'
```

`verify-full` 同时验证证书链与主机名，URL 中的主机名必须与服务器证书匹配。`require` 加密连接，但不校验主机名。

镜像基于 `scratch`，包含系统 CA 证书包与许可证，但没有 shell。公共受信任证书可使用内置根证书；使用私有 CA 且启用 `sslmode=verify-ca` 或 `verify-full` 时，仍需挂载私有 CA 并设置 `sslrootcert`。

## 缩小 HTTP 暴露面 {#minimize-http-exposure}

如果 Prometheus 与 exporter 在同一台主机上，只监听回环地址：

```bash
pg_exporter --web.listen-address=127.0.0.1:9630
```

需要远程抓取时，只允许监控网段通过防火墙或服务网格访问。同一监听端口同时提供指标与管理接口。

### TLS 与 Basic Auth {#tls-and-basic-auth}

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

请生成 bcrypt 哈希，不要把明文密码写进文件，例如使用 `htpasswd -nBC 10 prometheus`。mTLS、响应头与限流配置以 [exporter-toolkit Web 配置](https://github.com/prometheus/exporter-toolkit/blob/v0.20.0/docs/web-configuration.md)为准。

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

## 保护配置文件 {#protect-configuration-files}

发布软件包以较严格的权限将 `/etc/pg_exporter.yml` 与 `/etc/default/pg_exporter` 交给 `prometheus` 用户。复制或模板化文件时应保留相同的所有权与权限。数据库密码不应放在采集器 YAML 中；该文件用于查询和指标元数据，不是连接密钥。

部署前还要审查自定义 Label。数据库名、客户标识、租户名与 SQL 指纹都可能成为 Prometheus 标签，并继续流向远端存储、告警与仪表盘。

## 验证访问 {#verify-access}

启动 exporter 后，从 Prometheus 主机测试认证接口：

```bash
curl --cacert /etc/prometheus/ca/pg_exporter-ca.crt \
  --user prometheus https://db.example.com:9630/metrics
```

`curl` 会提示输入 HTTP 密码。确认服务器证书校验通过、响应中有 `pg_up 1`，并且 Prometheus 目标为 Up。启用 Basic Auth 后，不带凭据的请求应返回 `401`。

服务示例参见[生产部署](/zh/deploy/)，连接与采集器错误的定位方法参见[故障排查](/zh/troubleshooting/)。

## 工具链安全更新 {#toolchain-security-updates}

v1.6.0 使用 Go 1.27.3 与更新后的依赖，包括 `x/net` 0.62.0，并保留 v1.5.0 已记录的安全修复。[发布安全说明](/zh/release/v1.5.0/#security-updates)列出了纳入的 CVE 修复，并区分静态符号／包匹配与未导入模块的公告。升级时替换重新构建的二进制及配套采集器配置；仅更新主机编译器不会修复已有二进制。
