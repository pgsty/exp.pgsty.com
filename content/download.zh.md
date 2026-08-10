---
title: "下载 PG Exporter"
linkTitle: "下载"
description: "选择、安装、配置、启用并验证 PG Exporter 软件包、压缩包、容器、Pigsty 自动化或源码构建"
weight: 25
icon: fa-solid fa-download
categories: [指南]
---

PG Exporter {{< param version >}} 提供托管式 Linux 软件包、独立 RPM/DEB、Linux/macOS/Windows 发布压缩包、多架构容器镜像、Pigsty 自动化与源码构建。选择标准应当是生命周期由谁负责，而不是功能差异：每条路径运行的都是同一个导出器与同一套声明式采集器。

{{% alert title="产品名与交付物名称" color="info" %}}
产品名称写作 **PG Exporter**。Linux 软件包名是 `pg-exporter`；可执行文件、服务、配置文件与容器仓库继续保留兼容名称 `pg_exporter`。
{{% /alert %}}

{{< nav-cards cols="4" >}}
{{< nav-card title="Linux 软件包" link="#repository-packages" icon="fa-solid fa-box-archive" badge="推荐" desc="APT/YUM 生命周期、systemd 单元、合并配置与 /etc/default/pg_exporter。" />}}
{{< nav-card title="发布产物" link="#github-release-artifacts" icon="fa-solid fa-file-zipper" desc="带 SHA256 校验和的固定版本 RPM、DEB 及 Linux/macOS/Windows 压缩包。" />}}
{{< nav-card title="容器镜像" link="#container-image" icon="fa-brands fa-docker" desc="适用于 Docker、Podman、Compose 或编排平台的固定版本 amd64/arm64 镜像。" />}}
{{< nav-card title="Pigsty 或源码" link="#pigsty" icon="fa-solid fa-code-branch" desc="由 Pigsty 交付完整监控栈，或自行负责一个指定标签的完整构建。" />}}
{{< /nav-cards >}}

## 选择安装路径

| 方式 | 最适合 | 生命周期负责人 | 服务集成 |
|:---|:---|:---|:---|
| Pigsty APT/YUM 仓库 | 长期运行的 Linux 主机 | 操作系统包管理器 | 自带 systemd 单元与默认参数 |
| 独立 RPM/DEB | 固定版本或离线 Linux 晋级流程 | 你的制品流水线 | 自带 systemd 单元与默认参数 |
| 发布压缩包 | 极简安装、macOS/Windows、自定义目录 | 你 | 带服务示例，需要手工接线 |
| 容器镜像 | 容器平台 | 容器运行时或编排器 | 重启与密钥策略由你负责 |
| Pigsty | PostgreSQL 加完整可观测性栈 | Pigsty 自动化 | 集成指标、规则与仪表盘 |
| 源码 | 开发、审计、自定义构建 | 你 | 手工处理 |
{.full-width}

长期运行的 Linux 服务首选仓库软件包。升级、文件属主、`/etc/default/pg_exporter`、合并采集器配置与 systemd 行为都由同一个受管单元负责。

## 软件仓库 {#repository-packages}

`pigsty-infra` 仓库面向常见 EL 与 Debian/Ubuntu 平台发布 `pg-exporter`。

{{% tabpane text=true persist=header %}}
{{% tab header="APT · Debian / Ubuntu" selected=true %}}
```bash
sudo tee /etc/apt/sources.list.d/pigsty-infra.list > /dev/null <<'EOF'
deb [trusted=yes] https://repo.pigsty.io/apt/infra generic main
EOF

sudo apt update
sudo apt install -y pg-exporter
```
{{% /tab %}}
{{% tab header="YUM · RHEL / Rocky / Alma" %}}
```bash
sudo tee /etc/yum.repos.d/pigsty-infra.repo > /dev/null <<'EOF'
[pigsty-infra]
name=Pigsty Infra for $basearch
baseurl=https://repo.pigsty.io/yum/infra/$basearch
enabled=1
gpgcheck=0
module_hotfixes=1
EOF

sudo yum makecache
sudo yum install -y pg-exporter
```
{{% /tab %}}
{{% /tabpane %}}

这些示例与当前 Pigsty 软件包通道保持一致。如果你的供应链制度要求签名的软件仓库元数据，应当把校验过的发布产物晋级到自有仓库，而不是在生产主机上放宽制度。

### 配置并启用服务 {#enable-service}

软件包会安装：

- `/usr/bin/pg_exporter`：可执行文件；
- `/etc/pg_exporter.yml`：合并采集器配置，升级时保留；
- `/etc/default/pg_exporter`：进程环境变量与参数，升级时保留；
- `pg_exporter.service`：以 `prometheus` 用户运行的 systemd 单元。

先创建[数据库监控用户](/zh/start/#创建监控用户)，再写入连接 URL：

```bash
sudoedit /etc/default/pg_exporter

# 在文件中设置；生产环境优先使用 .pgpass 或密钥文件。
PG_EXPORTER_URL='postgres://monitor@127.0.0.1:5432/postgres?sslmode=disable'
```

启用、启动并验证服务：

```bash
sudo systemctl enable --now pg_exporter
sudo systemctl status pg_exporter
journalctl -u pg_exporter -n 50 --no-pager

curl -fsS http://127.0.0.1:9630/up
curl -fsS http://127.0.0.1:9630/metrics | grep '^pg_up '
```

远程生产目标应使用 `sslmode=verify-full` 并明确配置 CA。[部署指南](/zh/deploy/#监控用户与凭据)详细说明 `.pgpass`、`PG_EXPORTER_URL_FILE`、HTTP TLS/认证与网络暴露策略。

## GitHub 发布产物 {#github-release-artifacts}

[v{{< param version >}} 版本](https://github.com/pgsty/pg_exporter/releases/tag/v{{< param version >}})包含 RPM、DEB，以及 Linux、macOS、Windows 压缩包。Linux 支持 amd64、arm64、ppc64le；macOS 支持 amd64、arm64；Windows 提供 amd64。

{{% tabpane text=true persist=header %}}
{{% tab header="DEB 软件包" selected=true %}}
根据发布文件名选择 `ARCH=amd64`、`arm64` 或 `ppc64le`：

```bash
VERSION={{< param version >}}
ARCH=amd64
curl -fLO "https://github.com/pgsty/pg_exporter/releases/download/v${VERSION}/pg-exporter_${VERSION}-1_${ARCH}.deb"
sudo apt install "./pg-exporter_${VERSION}-1_${ARCH}.deb"
```

然后继续[配置服务](#enable-service)。
{{% /tab %}}
{{% tab header="RPM 软件包" %}}
在受支持平台上，`uname -m` 会返回发布产物使用的 `x86_64`、`aarch64` 或 `ppc64le`：

```bash
VERSION={{< param version >}}
ARCH=$(uname -m)
curl -fLO "https://github.com/pgsty/pg_exporter/releases/download/v${VERSION}/pg-exporter-${VERSION}-1.${ARCH}.rpm"
sudo dnf install "./pg-exporter-${VERSION}-1.${ARCH}.rpm"
```

然后继续[配置服务](#enable-service)。
{{% /tab %}}
{{% tab header="Tar 压缩包" %}}
`OS` 可选 `linux` 或 `darwin`；`ARCH` 可选 `amd64`、`arm64` 或仅 Linux 支持的 `ppc64le`。Windows 用户下载 `windows-amd64` 压缩包，并从自选目录运行 `pg_exporter.exe`。

```bash
VERSION={{< param version >}}
OS=linux
ARCH=amd64
ARCHIVE="pg_exporter-${VERSION}.${OS}-${ARCH}.tar.gz"
STAGE="pg_exporter-${VERSION}-${OS}-${ARCH}"

curl -fLO "https://github.com/pgsty/pg_exporter/releases/download/v${VERSION}/${ARCHIVE}"
mkdir -p "${STAGE}"
tar -xzf "${ARCHIVE}" -C "${STAGE}"
sudo install -m 0755 "${STAGE}/pg_exporter" /usr/local/bin/pg_exporter
sudo install -m 0644 "${STAGE}/pg_exporter.yml" /etc/pg_exporter.yml

pg_exporter --version
```

你可以用 `PG_EXPORTER_URL=... pg_exporter` 直接运行，或按自己的路径调整压缩包内的 `package/pg_exporter.service` 与 `package/pg_exporter.default` 示例。
{{% /tab %}}
{{% /tabpane %}}

### 校验下载文件

每个版本都附带 `checksums.txt`。请先校验，再安装或晋级：

```bash
VERSION={{< param version >}}
curl -fLO "https://github.com/pgsty/pg_exporter/releases/download/v${VERSION}/checksums.txt"
sha256sum -c checksums.txt --ignore-missing
```

macOS 可以执行 `shasum -a 256 <archive>`，并与 `checksums.txt` 中对应条目比较。

## 容器镜像 {#container-image}

官方 [`pgsty/pg_exporter`](https://hub.docker.com/r/pgsty/pg_exporter) 镜像提供 amd64 与 arm64 清单。生产部署请固定版本标签：

```bash
docker run -d \
  --name pg_exporter \
  --restart unless-stopped \
  -p 127.0.0.1:9630:9630 \
  -e PG_EXPORTER_URL='postgres://monitor:S3cret@postgres:5432/postgres' \
  pgsty/pg_exporter:{{< param version >}}

curl -fsS http://127.0.0.1:9630/up
curl -fsS http://127.0.0.1:9630/metrics | grep '^pg_up '
```

只有在确实需要自定义时才挂载采集器配置：

```bash
docker run -d \
  --name pg_exporter \
  --restart unless-stopped \
  -p 127.0.0.1:9630:9630 \
  -e PG_EXPORTER_URL_FILE=/run/secrets/pgurl \
  -v ./pgurl:/run/secrets/pgurl:ro \
  -v ./pg_exporter.yml:/etc/pg_exporter.yml:ro \
  pgsty/pg_exporter:{{< param version >}}
```

{{% alert title="Scratch 镜像" color="warning" %}}
镜像只包含静态导出器、合并配置与许可证，没有 Shell 或操作系统 CA 包。使用 `sslmode=verify-ca` 或 `verify-full` 时必须明确挂载所需 CA。
{{% /alert %}}

Compose、Kubernetes、探针、密钥与 Prometheus 接线示例见[容器与 Kubernetes 部署](/zh/deploy/#docker-部署)。

## Pigsty {#pigsty}

如果你需要 PG Exporter 加 PostgreSQL 发行版、Prometheus 兼容指标存储、记录/告警规则与 Grafana 仪表盘，[Pigsty](https://pigsty.cc/) 是完整集成路径。

```bash
curl -fsSL https://repo.pigsty.io/get | bash
cd ~/pigsty
```

这段引导命令只负责获取 Pigsty；对任何主机执行部署前，都应选择正确的配置清单与部署流程。后续参阅 [Pigsty 安装指南](https://pigsty.cc/docs/setup/install/)及其现有 PostgreSQL 监控流程。

## 从源码构建

使用版本标签 `go.mod` 声明的 Go 版本，并构建精确的发布源码：

```bash
git clone https://github.com/pgsty/pg_exporter.git
cd pg_exporter
git checkout "v{{< param version >}}"
make build

./pg_exporter --version
PG_EXPORTER_URL='postgres://monitor@127.0.0.1:5432/postgres' ./pg_exporter --dry-run
```

在 Unix 上手工安装：

```bash
sudo install -m 0755 pg_exporter /usr/local/bin/pg_exporter
sudo install -m 0644 pg_exporter.yml /etc/pg_exporter.yml
```

源码构建不会创建服务用户，也不会注册系统服务。如果需要软件包级别的属主与服务行为，请使用 RPM/DEB，或明确复现这些控制。

## 启用检查清单

只有目标可以被抓取，安装才算完成：

1. 创建最小权限的[监控用户](/zh/start/#创建监控用户)。
2. 通过 `--url`、`PG_EXPORTER_URL`、`PGURL` 或 `PG_EXPORTER_URL_FILE` 提供连接。
3. 执行 `pg_exporter --dry-run` 并检查 [`/explain`](/zh/api/#get-explain)。
4. 验证 `/up`，并确认 `/metrics` 中出现 `pg_up 1`。
5. 将导出器加入 [Prometheus 兼容抓取](/zh/start/#接入-prometheus)。
6. 生产环境还要检查[凭据、TLS、HTTP 暴露、systemd/容器重启策略与探针](/zh/deploy/)。

需要完整制品矩阵或 PostgreSQL/PgBouncer 兼容性细节？请继续查看[安装参考](/zh/install/)与[兼容性矩阵](/zh/compatibility/)。
