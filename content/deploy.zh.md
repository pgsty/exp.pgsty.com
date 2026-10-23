---
title: "生产部署"
linkTitle: "部署指南"
description: "使用 systemd、Docker 或 Kubernetes 运行 pg_exporter 并接入 Prometheus"
weight: 50
icon: fa-solid fa-server
categories: [参考]
---

先[安装软件包](/zh/install/)、创建监控角色，再选择下文的 systemd、Docker 或 Kubernetes 部署方式。启动后检查 `/metrics`，并将 exporter 接入 Prometheus。

[命令参考](/zh/cmd/)列出参数、环境变量、默认值与优先级。命令行设置优先于对应的环境变量；日志、动作与 exporter-toolkit Web 参数只提供命令行形式。采集 SQL 与指标定义使用 [YAML 配置](/zh/config/)。

## 进程设置

以下前台运行示例通过 `.pgpass` 提供数据库密码：

```bash
pg_exporter \
  --url='postgres://monitor@localhost:5432/postgres' \
  --config=/etc/pg_exporter.yml \
  --web.listen-address=:9630 \
  --log.level=info
```

自动发现默认启用。启动时数据库不可用，exporter 仍会启动 HTTP 服务并在后台重试。设置 `--fail-fast` 后，初次数据库检查失败会使进程退出。

### 连接 URL 的来源

使用 `--url` 或 `PG_EXPORTER_URL` 指定目标，也可通过 `PG_EXPORTER_URL_FILE` 读取密钥文件。完整[优先级规则](/zh/cmd/#目标与配置优先级)见命令参考。URL 未指定 `sslmode` 时会使用 `disable`；远程 TLS 连接需显式设置该参数。

使用 URL 文件时，清除 `PG_EXPORTER_URL`、`PGURL`，并省略 `--url`。软件包服务还需删除 `/etc/default/pg_exporter` 中默认的 `PG_EXPORTER_URL` 行。

## 监控用户与凭据

### 创建监控用户

```sql
CREATE ROLE monitor WITH LOGIN PASSWORD 'replace-this-secret' CONNECTION LIMIT 5;
GRANT pg_monitor TO monitor;   -- PostgreSQL 10+
```

主目标连接池最多三个连接，每个额外发现的数据库最多一个。按这个总量及共用角色的 exporter 数量设置 `CONNECTION LIMIT`。如果角色没有目标库的 `CONNECT` 权限，需要逐库授权；可选视图与扩展可能需要额外授权，参见[安全指南](/zh/security/)。

### 使用 .pgpass 管理密码

把密码从 URL 中拿掉，交给 libpq 的 `.pgpass` 机制：

```bash
# 以运行 exporter 的操作系统用户身份创建
umask 077
printf '%s\n' 'localhost:5432:*:monitor:replace-this-secret' > ~/.pgpass
chmod 600 ~/.pgpass

# URL 中不再携带密码
export PG_EXPORTER_URL='postgres://monitor@localhost:5432/postgres'
```

软件包服务使用 `prometheus` 用户。先用 `getent passwd prometheus` 检查主目录，再把 `.pgpass` 安装到该目录。软件包新建账号的主目录为 `/var/lib/prometheus`，目录与文件的安装命令见[安全指南](/zh/security/#pgpass)。

### 数据库连接 TLS

```bash
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pg_exporter/ca.crt'
```

### HTTP 端口侧的保护

`/metrics` 之外，`/reload`、`/explain`、`/stat` 属于管理端点：能访问该端口的任何人都可以读取配置与运行态信息、触发重载。如果 exporter 暴露在共享网络中，请通过 `--web.config.file`（[exporter-toolkit web 配置](https://github.com/prometheus/exporter-toolkit/blob/v0.20.0/docs/web-configuration.md)）启用 TLS/Basic Auth，或在防火墙/反向代理层限制来源。

## Systemd 部署（RPM/DEB 包）

软件包将二进制安装到 `/usr/bin/pg_exporter`，采集器安装到 `/etc/pg_exporter.yml`，运行设置放在 `/etc/default/pg_exporter`。RPM 的服务单元位于 `/usr/lib/systemd/system/pg_exporter.service`，DEB 位于 `/lib/systemd/system/pg_exporter.service`：

```ini
# /usr/lib/systemd/system/pg_exporter.service
[Unit]
Description=Prometheus exporter for PostgreSQL/Pgbouncer server metrics
Documentation=https://pigsty.io/docs/pg_exporter
After=network.target

[Service]
EnvironmentFile=-/etc/default/pg_exporter
User=prometheus
ExecStart=/usr/bin/pg_exporter $PG_EXPORTER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

环境文件 `/etc/default/pg_exporter`（包默认值）：

```bash
PG_EXPORTER_URL='postgres://:5432/postgres?sslmode=disable'
PG_EXPORTER_CONFIG=/etc/pg_exporter.yml
PG_EXPORTER_LABEL=""
PG_EXPORTER_TAG=""
PG_EXPORTER_DISABLE_CACHE=false
PG_EXPORTER_AUTO_DISCOVERY=true
PG_EXPORTER_EXCLUDE_DATABASE="template0,template1,postgres"
PG_EXPORTER_INCLUDE_DATABASE=""
PG_EXPORTER_NAMESPACE="pg"
PG_EXPORTER_FAIL_FAST=false
PG_EXPORTER_CONNECT_TIMEOUT=100
PG_EXPORTER_TELEMETRY_PATH="/metrics"
PG_EXPORTER_OPTS='--log.level=info'
```

将默认 URL 改为实际监控用户与目标。有环境变量别名的设置（如 `PG_EXPORTER_DISABLE_INTRO`）可直接追加；只有命令行形式的参数放入 `PG_EXPORTER_OPTS`。软件包将环境文件和采集配置标记为配置文件，升级时保留本地修改。

启动并验证服务：

```bash
sudo systemctl enable --now pg_exporter
sudo systemctl status pg_exporter --no-pager
curl -fsS http://127.0.0.1:9630/metrics
sudo journalctl -u pg_exporter -n 50 --no-pager
```

确认指标中有 `pg_up 1`。持续查看日志可运行 `sudo journalctl -u pg_exporter -f`。

修改 `/etc/default/pg_exporter` 后执行 `sudo systemctl restart pg_exporter`。只修改采集器 YAML 时，可直接重载：

```bash
curl -fsS -X POST http://127.0.0.1:9630/reload
```

## Docker 部署

将实际数据库连接 URL 写入 `pg_exporter.url`。此例要求数据库证书与 `db.example.com` 匹配，并准备 CA 文件 `ca.crt`：

```text
postgres://monitor:replace-this-secret@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/run/secrets/pg-ca.crt
```

限制 URL 文件权限，再将它与 CA 挂载到容器：

```bash
chmod 600 pg_exporter.url
docker run -d \
  --name pg_exporter \
  --restart unless-stopped \
  -p 9630:9630 \
  -v "$PWD/pg_exporter.url:/run/secrets/pg_exporter_url:ro" \
  -v "$PWD/ca.crt:/run/secrets/pg-ca.crt:ro" \
  -e PG_EXPORTER_URL_FILE=/run/secrets/pg_exporter_url \
  pgsty/pg_exporter:{{< param version >}}
```

Docker Compose:

```yaml
services:
  pg_exporter:
    image: pgsty/pg_exporter:{{< param version >}}
    restart: unless-stopped
    ports:
      - "9630:9630"
    environment:
      PG_EXPORTER_URL_FILE: /run/secrets/pg_exporter_url
    volumes:
      - ./pg_exporter.url:/run/secrets/pg_exporter_url:ro
      - ./ca.crt:/run/secrets/pg-ca.crt:ro
```

镜像已内置默认采集配置。需要替换时，将自定义文件只读挂载到 `/etc/pg_exporter.yml`。镜像基于 `scratch`，没有 Shell 和 CA 证书包，因此上面的 TLS 示例需要挂载 CA。

检查容器：

```bash
docker logs pg_exporter
curl -fsS http://127.0.0.1:9630/metrics
```

将 9630 端口发布到 Prometheus 可达的地址，并限制网络来源。如果 Prometheus 就在 Docker 宿主机上，使用 `-p 127.0.0.1:9630:9630`。

## Kubernetes 部署

在 exporter 所在命名空间中，用上述 URL 与 CA 文件创建 Secret：

```bash
kubectl create secret generic pg-exporter-connection \
  --from-file=connection-url=./pg_exporter.url \
  --from-file=pg-ca.crt=./ca.crt
```

将下面的清单保存为 `pg-exporter.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pg-exporter
spec:
  replicas: 1
  selector:
    matchLabels: { app: pg-exporter }
  template:
    metadata:
      labels: { app: pg-exporter }
    spec:
      containers:
      - name: pg-exporter
        image: pgsty/pg_exporter:{{< param version >}}
        ports:
        - { name: metrics, containerPort: 9630 }
        env:
        - name: PG_EXPORTER_URL_FILE
          value: /run/secrets/connection-url
        volumeMounts:
        - name: connection
          mountPath: /run/secrets
          readOnly: true
        livenessProbe:
          httpGet: { path: /version, port: metrics }
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet: { path: /version, port: metrics }
          periodSeconds: 5
        resources:
          requests: { cpu: 100m, memory: 128Mi }
          limits: { cpu: 200m, memory: 256Mi }
      volumes:
      - name: connection
        secret:
          secretName: pg-exporter-connection
---
apiVersion: v1
kind: Service
metadata:
  name: pg-exporter
spec:
  ports:
  - { port: 9630, targetPort: metrics, name: metrics }
  selector: { app: pg-exporter }
```

两个探针都用 `/version` 检查 exporter 是否能响应 HTTP。`/liveness`、`/readiness` 实际上是 `/up` 的别名，反映数据库健康状态。将它们用于此处，会在数据库故障时重启 exporter 或移除 Service 端点，反而失去故障期间需要的指标。

应用清单并检查部署结果：

```bash
kubectl apply -f pg-exporter.yaml
kubectl rollout status deployment/pg-exporter
kubectl logs deployment/pg-exporter
kubectl port-forward service/pg-exporter 9630:9630
```

保持端口转发运行，在另一个终端检查 `/metrics`。按实际采集负载调整资源请求与上限；若启用 HTTP 认证，探针也需要相应凭据。

## 自动发现

自动发现会将同一 PostgreSQL 实例中的数据库加入监控。可用包含名单限定范围：

```bash
pg_exporter --auto-discovery \
  --exclude-database="template0,template1,postgres" \
  --include-database="app,analytics"
```

URL 指定的数据库始终会被监控。包含/排除名单只作用于额外数据库；同一个名称同时出现在两份名单时，排除优先。包含名单为空时，允许所有其他符合条件的数据库。

- 集群级采集器（`tags: [cluster]`）只在主连接上执行一次。
- 数据库级采集器也在发现的数据库上执行。内置采集器用 `datname` 标签区分结果；自定义 SQL 需自行返回声明的标签列。
- 每次抓取检查数据库的新增或删除。
- `--no-auto-discovery` 将采集范围限定在 URL 指定的数据库。

## 监控 PgBouncer

将 URL 的数据库名设为 `pgbouncer` 即可切换到 PgBouncer 模式（以此触发自动检测）：

```bash
PG_EXPORTER_URL='postgres://stats_user@localhost:6432/pgbouncer' \
pg_exporter --namespace=pgbouncer --web.listen-address=:9631
```

在 PgBouncer 中配置该账号的认证，并将其加入 `stats_users`，密码存入 `.pgpass`。此模式运行 PgBouncer 的 `SHOW` 采集器。分别为 PostgreSQL 与 PgBouncer 启动 exporter，使用不同端口。

未指定命名空间时，自监控指标默认使用 `pgbouncer` 前缀。软件包环境文件设置了 `PG_EXPORTER_NAMESPACE=pg`，部署 PgBouncer 服务时应改为 `pgbouncer`。该设置只影响内置自监控指标，不改变 YAML 定义的指标名。

## Prometheus 抓取与告警

### 抓取配置

```yaml
scrape_configs:
  - job_name: 'postgresql'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ['pg-1:9630', 'pg-2:9630', 'pg-3:9630']
```

Kubernetes 服务发现：

```yaml
scrape_configs:
  - job_name: 'postgresql'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: pg-exporter
        action: keep
      - source_labels: [__meta_kubernetes_pod_container_port_name]
        regex: metrics
        action: keep
```

可先使用 15 秒抓取间隔与 10 秒超时。采集结果在 `ttl` 到期前可以复用，内置采集器常用 10 秒 TTL。缩短间隔或增加监控库之前，先测量完整抓取的耗时。

### 告警规则

以下示例使用默认的 `pg` 自监控指标命名空间：

```yaml
groups:
  - name: pg_exporter
    rules:
      # 导出器进程失联
      - alert: PgExporterDown
        expr: up{job="postgresql"} == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "pg_exporter 宕机 ({{ $labels.instance }})"

      # 主目标连接或 fatal 采集器失败
      - alert: PostgreSQLDown
        expr: pg_up{job="postgresql"} == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "PostgreSQL 抓取失败 ({{ $labels.instance }})"

      # 整体抓取耗时异常（单位：秒）
      - alert: PgExporterSlowScrape
        expr: pg_exporter_scrape_duration{job="postgresql"} > 8
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "pg_exporter 抓取缓慢 ({{ $labels.instance }})"
```

### 基于角色的流量路由

`/primary`、`/replica`、`/read` 等健康检查端点可以直接充当 HAProxy 等负载均衡器的健康检查探针，实现主从读写分离。端点语义与完整的 HAProxy 配置示例见 [API 参考](/zh/api/#流量路由)。
