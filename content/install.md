---
title: "Installation"
linkTitle: "Installation"
description: "Install pg_exporter from packages, release archives, containers, Pigsty, or source"
weight: 30
icon: fa-solid fa-cloud-arrow-down
categories: [Reference]
---

`pg_exporter` can be installed via Pigsty, YUM/APT repositories, GitHub release packages (RPM/DEB/Tarball), Docker images, or built from source — pick whichever fits your infrastructure.

## Pigsty

The easiest way to get started with `pg_exporter` is to use [Pigsty](https://pigsty.io),
which is a complete PostgreSQL distribution with built-in Observability best practices based on `pg_exporter`, Prometheus, and Grafana.
You don't even need to know any details about `pg_exporter`; it just gives you all the metrics and dashboard panels.

```bash
curl -fsSL https://repo.pigsty.io/get | bash; cd ~/pigsty;
```

## Release

You can also download `pg_exporter` package (`RPM`/`DEB`/ Tarball) directly from the [Latest GitHub Release Page](https://github.com/pgsty/pg_exporter/releases/latest):

**v1.4.1 Release Files:**

| Type                    | File                                                                                                                                           |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| DEB (amd64)             | [pg-exporter_1.4.1-1_amd64.deb](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg-exporter_1.4.1-1_amd64.deb)                   |
| DEB (arm64)             | [pg-exporter_1.4.1-1_arm64.deb](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg-exporter_1.4.1-1_arm64.deb)                   |
| DEB (ppc64le)           | [pg-exporter_1.4.1-1_ppc64le.deb](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg-exporter_1.4.1-1_ppc64le.deb)               |
| RPM (aarch64)           | [pg-exporter-1.4.1-1.aarch64.rpm](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg-exporter-1.4.1-1.aarch64.rpm)               |
| RPM (x86_64)            | [pg-exporter-1.4.1-1.x86_64.rpm](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg-exporter-1.4.1-1.x86_64.rpm)                 |
| RPM (ppc64le)           | [pg-exporter-1.4.1-1.ppc64le.rpm](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg-exporter-1.4.1-1.ppc64le.rpm)               |
| Tarball (Linux amd64)   | [pg_exporter-1.4.1.linux-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg_exporter-1.4.1.linux-amd64.tar.gz)     |
| Tarball (Linux arm64)   | [pg_exporter-1.4.1.linux-arm64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg_exporter-1.4.1.linux-arm64.tar.gz)     |
| Tarball (Linux ppc64le) | [pg_exporter-1.4.1.linux-ppc64le.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg_exporter-1.4.1.linux-ppc64le.tar.gz) |
| Tarball (macOS amd64)   | [pg_exporter-1.4.1.darwin-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg_exporter-1.4.1.darwin-amd64.tar.gz)   |
| Tarball (macOS arm64)   | [pg_exporter-1.4.1.darwin-arm64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg_exporter-1.4.1.darwin-arm64.tar.gz)   |
| Tarball (Windows amd64) | [pg_exporter-1.4.1.windows-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v1.4.1/pg_exporter-1.4.1.windows-amd64.tar.gz) |

You can install it directly with your OS package manager (`rpm`/`dpkg`), or just place the binary in your `$PATH`. Current tarballs also include `pg_exporter.yml`, `package/pg_exporter.default`, `package/pg_exporter.service`, and `LICENSE` for manual deployments.

{{% alert title="RPM package rename" color="info" %}}
Starting with `v1.4.1`, the official RPM package name and artifact prefix change from `pg_exporter` to `pg-exporter`, matching the DEB package and repository install commands. The new RPM also provides and obsoletes the legacy `pg_exporter` package name, allowing direct upgrades from earlier releases.
{{% /alert %}}

Full SHA256 checksums are available in `checksums.txt` on the release page; version-specific checksums are also archived in the [release notes](/release/).

## Repository

The `pg_exporter` package is also available in the [`pigsty-infra`](https://ext.pgsty.com/repo/infra) repo.
You can add the repo to your system and install it with your OS package manager:

### YUM

For EL distributions such as RHEL, Rocky Linux, CentOS, AlmaLinux, and Oracle Linux:

```bash
sudo tee /etc/yum.repos.d/pigsty-infra.repo > /dev/null <<-'EOF'
[pigsty-infra]
name=Pigsty Infra for $basearch
baseurl=https://repo.pigsty.io/yum/infra/$basearch
enabled = 1
gpgcheck = 0
module_hotfixes=1
EOF

sudo yum makecache;
sudo yum install -y pg-exporter
```

### APT

For Debian, Ubuntu and compatible Linux Distributions:

```bash
sudo tee /etc/apt/sources.list.d/pigsty-infra.list > /dev/null <<EOF
deb [trusted=yes] https://repo.pigsty.io/apt/infra generic main
EOF

sudo apt update;
sudo apt install -y pg-exporter
```

## Docker

We have prebuilt docker images for `amd64` and `arm64` architectures on docker hub: [pgsty/pg_exporter](https://hub.docker.com/r/pgsty/pg_exporter).

```bash
# Basic usage
docker run -d \
  --name pg_exporter \
  -p 9630:9630 \
  -e PG_EXPORTER_URL="postgres://user:password@host:5432/postgres" \
  pgsty/pg_exporter:latest

# With custom configuration
docker run -d \
  --name pg_exporter \
  -p 9630:9630 \
  -v /path/to/pg_exporter.yml:/etc/pg_exporter.yml:ro \
  -e PG_EXPORTER_CONFIG="/etc/pg_exporter.yml" \
  -e PG_EXPORTER_URL="postgres://user:password@host:5432/postgres" \
  pgsty/pg_exporter:latest

# With auto-discovery enabled
docker run -d \
  --name pg_exporter \
  -p 9630:9630 \
  -e PG_EXPORTER_URL="postgres://user:password@host:5432/postgres" \
  -e PG_EXPORTER_AUTO_DISCOVERY="true" \
  -e PG_EXPORTER_EXCLUDE_DATABASE="template0,template1" \
  pgsty/pg_exporter:latest
```

{{% alert title="Warning" color="warning" %}}
The current Docker image is built from `scratch`. If you connect to remote PostgreSQL with `sslmode=verify-ca` or `verify-full`, mount an explicit CA certificate (`sslrootcert` or a system CA bundle), otherwise TLS verification may fail.
{{% /alert %}}

## Compatibility

The default configuration supports PostgreSQL 10-19+. For EOL PostgreSQL versions, use the bundled `legacy/` config package for compatible monitoring.

| PostgreSQL Version | Support Status                  |
|--------------------|---------------------------------|
| 10 ~ 19+           | ✅ Full Support (default config) |
| 9.1 ~ 9.6          | ⚠️ Use `legacy/pg_exporter.yml` |
| 9.0 and earlier    | ❌ Unsupported                   |

Legacy config example:

```bash
make conf9
PG_EXPORTER_CONFIG=legacy/pg_exporter.yml pg_exporter
```

pg_exporter works with pgBouncer 1.8+, since `v1.8` is the first version with `SHOW` command support.

| pgBouncer Version | Support Status |
|-------------------|----------------|
| 1.8.x ~ 1.25+     | ✅ Full Support |
| before 1.8.x      | ⚠️ No Metrics  |
