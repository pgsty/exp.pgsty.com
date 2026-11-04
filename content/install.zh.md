---
title: "安装指南"
linkTitle: "安装指南"
description: "通过软件包、发布压缩包、容器、Pigsty 或源码安装 PG Exporter"
weight: 30
icon: fa-solid fa-download
categories: [参考]
---

Linux 服务可选择软件包，独立运行可选择发布压缩包，Docker 与 Kubernetes 使用容器镜像。[下载页面](/zh/download/)提供各方式的对照与安装命令，本页列出发布文件和仓库配置。

## Pigsty

[Pigsty](https://pigsty.cc) 将 PG Exporter 与指标存储、告警规则和 Grafana 仪表盘一起部署。以下命令下载 Pigsty；随后按[安装指南](https://pigsty.cc/docs/setup/install/)配置并部署监控栈。

```bash
curl -fsSL https://repo.pigsty.io/get | bash
cd ~/pigsty
```

## 发布版本

从 [GitHub 发布页面](https://github.com/pgsty/pg_exporter/releases/latest)下载 RPM、DEB 或压缩包：

**v{{< param version >}} 发布文件：**

| 类型                      | 文件                                                                                                                                               |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| DEB (amd64)             | [pg-exporter_{{< param version >}}-1_amd64.deb](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter_{{< param version >}}-1_amd64.deb)                     |
| DEB (arm64)             | [pg-exporter_{{< param version >}}-1_arm64.deb](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter_{{< param version >}}-1_arm64.deb)                     |
| DEB (ppc64le)           | [pg-exporter_{{< param version >}}-1_ppc64le.deb](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter_{{< param version >}}-1_ppc64le.deb)                 |
| RPM (aarch64)           | [pg-exporter-{{< param version >}}-1.aarch64.rpm](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter-{{< param version >}}-1.aarch64.rpm)                 |
| RPM (x86_64)            | [pg-exporter-{{< param version >}}-1.x86_64.rpm](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter-{{< param version >}}-1.x86_64.rpm)                   |
| RPM (ppc64le)           | [pg-exporter-{{< param version >}}-1.ppc64le.rpm](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter-{{< param version >}}-1.ppc64le.rpm)                 |
| Tarball (Linux amd64)   | [pg_exporter-{{< param version >}}.linux-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.linux-amd64.tar.gz)       |
| Tarball (Linux arm64)   | [pg_exporter-{{< param version >}}.linux-arm64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.linux-arm64.tar.gz)       |
| Tarball (Linux ppc64le) | [pg_exporter-{{< param version >}}.linux-ppc64le.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.linux-ppc64le.tar.gz)   |
| Tarball (macOS amd64)   | [pg_exporter-{{< param version >}}.darwin-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.darwin-amd64.tar.gz)     |
| Tarball (macOS arm64)   | [pg_exporter-{{< param version >}}.darwin-arm64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.darwin-arm64.tar.gz)     |
| Tarball (Windows amd64) | [pg_exporter-{{< param version >}}.windows-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.windows-amd64.tar.gz)   |
{.full-width .wide .expand}

下载 RPM 后用 `sudo dnf install ./<package>.rpm` 安装，DEB 用 `sudo apt install ./<package>.deb`。压缩包解压后，将二进制安装到 `$PATH` 中。压缩包还包含 `pg_exporter.yml`、`package/pg_exporter.default`、`package/pg_exporter.service` 与 `LICENSE`。

安装后运行 `pg_exporter --version`。软件包用户按[部署指南](/zh/deploy/#systemd-部署rpmdeb-包)启动 systemd 服务；压缩包用户准备监控凭据后，按[前台运行示例](/zh/deploy/#进程设置)启动。

> [!NOTE] RPM 包名变更
> 自 `v1.4.1` 起，官方 RPM 的包名及文件名前缀由 `pg_exporter` 统一为 `pg-exporter`，与 DEB 及仓库安装命令保持一致。新 RPM 同时声明兼容并替换旧包名 `pg_exporter`，可直接从旧版升级。

从同一版本的发布页面下载 `checksums.txt`，安装前校验文件。Linux 可在下载目录运行 `sha256sum -c checksums.txt --ignore-missing`，已下载的每个制品都应显示 `OK`。macOS 使用 `shasum -a 256 <file>`，将结果与 `checksums.txt` 中对应行比较。

## 软件仓库

`pg-exporter` 软件包也可以在 [`pigsty-infra`](https://ext.pgsty.com/repo/infra) 仓库中获取。您可以将该仓库添加到系统中，然后使用操作系统包管理器安装：

### YUM

适用于 RHEL、RockyLinux、CentOS、Alma Linux、OracleLinux 等 EL 系发行版：

```bash
curl -fsSL https://repo.pigsty.io/key | sudo tee /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty >/dev/null
sudo tee /etc/yum.repos.d/pigsty-infra.repo > /dev/null <<-'EOF'
[pigsty-infra]
name=Pigsty Infra for $basearch
baseurl=https://repo.pigsty.io/yum/infra/$basearch
enabled = 1
gpgcheck = 1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
module_hotfixes=1
EOF

sudo yum makecache
sudo yum install -y pg-exporter
```

### APT

适用于 Debian、Ubuntu 及兼容的 Linux 发行版：

```bash
sudo apt update
sudo apt install -y curl gnupg
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://repo.pigsty.io/key | gpg --dearmor | sudo tee /etc/apt/keyrings/pigsty.gpg >/dev/null
sudo chmod 0644 /etc/apt/keyrings/pigsty.gpg
sudo tee /etc/apt/sources.list.d/pigsty-infra.list > /dev/null <<'EOF'
deb [signed-by=/etc/apt/keyrings/pigsty.gpg] https://repo.pigsty.io/apt/infra generic main
EOF

sudo apt update
sudo apt install -y pg-exporter
```

## Docker

[官方镜像](https://hub.docker.com/r/pgsty/pg_exporter)支持 Linux amd64 与 arm64。拉取并确认需要部署的版本：

```bash
docker pull pgsty/pg_exporter:{{< param version >}}
docker run --rm pgsty/pg_exporter:{{< param version >}} --version
```

镜像内置 `/etc/pg_exporter.yml`，自定义采集器可挂载到该路径。自动发现默认启用，设置 `PG_EXPORTER_AUTO_DISCOVERY=false` 即可关闭。

按 [Docker 部署示例](/zh/deploy/#docker-部署)挂载连接密钥并启动容器。镜像基于 `scratch`，没有 CA 证书包；使用 `sslmode=verify-ca` 或 `verify-full` 时，需挂载 CA 文件。

## 从源码构建

检出发布标签，使用其 `go.mod` 声明的 Go 版本（v1.5.0 要求 Go 1.27.3 或更高版本）：

```bash
git clone --depth 1 --branch v{{< param version >}} https://github.com/pgsty/pg_exporter.git pg_exporter-src
cd pg_exporter-src
go build -ldflags='-X pg_exporter/exporter.Version=v{{< param version >}}' -o /tmp/pg_exporter .
/tmp/pg_exporter --version
sudo install -m 0755 /tmp/pg_exporter /usr/local/bin/pg_exporter
sudo install -m 0644 pg_exporter.yml /etc/pg_exporter.yml
```

源码安装的二进制位于 `/usr/local/bin/pg_exporter`，可按[前台运行示例](/zh/deploy/#进程设置)启动。需要 systemd 服务时，推荐安装 RPM/DEB 软件包；软件包会配置运行账号及使用 `/usr/bin/pg_exporter` 的服务单元。

## 兼容性

PostgreSQL 10 及更高版本使用默认配置，其中已包含 PostgreSQL 19 分支。PostgreSQL 9.1–9.6 需要对应源码标签中的 `legacy/pg_exporter.yml`，二进制发布压缩包不包含该文件。

在上述源码目录中运行：

```bash
pg_exporter --config=legacy/pg_exporter.yml --url='postgres://monitor@localhost:5432/postgres'
```

内置 PgBouncer 采集器要求 1.8 或更高版本。版本选择、体系结构与采集器前置条件见[兼容性](/zh/compatibility/)。
