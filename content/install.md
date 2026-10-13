---
title: "Installation"
linkTitle: "Installation"
description: "Install PG Exporter from packages, release archives, containers, Pigsty, or source"
weight: 30
icon: fa-solid fa-cloud-arrow-down
categories: [Reference]
---

Use a Linux package for a managed service, a release archive for a standalone binary, or a container for Docker and Kubernetes. [Download](/download/) compares these options and provides installation commands. This page lists the release files and repository setup.

## Pigsty

[Pigsty](https://pigsty.io) deploys PG Exporter with metrics storage, alert rules, and Grafana dashboards. The command below downloads Pigsty; follow its [installation guide](https://pigsty.io/docs/setup/install/) to configure and deploy the monitoring stack.

```bash
curl -fsSL https://repo.pigsty.io/get | bash
cd ~/pigsty
```

## Release

Download RPM, DEB, or tarball files from the [latest GitHub release](https://github.com/pgsty/pg_exporter/releases/latest):

**v{{< param version >}} Release Files:**

| Type                    | File                                                                                                                                           |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| DEB (amd64)             | [pg-exporter_{{< param version >}}-1_amd64.deb](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter_{{< param version >}}-1_amd64.deb)                   |
| DEB (arm64)             | [pg-exporter_{{< param version >}}-1_arm64.deb](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter_{{< param version >}}-1_arm64.deb)                   |
| DEB (ppc64le)           | [pg-exporter_{{< param version >}}-1_ppc64le.deb](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter_{{< param version >}}-1_ppc64le.deb)               |
| RPM (aarch64)           | [pg-exporter-{{< param version >}}-1.aarch64.rpm](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter-{{< param version >}}-1.aarch64.rpm)               |
| RPM (x86_64)            | [pg-exporter-{{< param version >}}-1.x86_64.rpm](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter-{{< param version >}}-1.x86_64.rpm)                 |
| RPM (ppc64le)           | [pg-exporter-{{< param version >}}-1.ppc64le.rpm](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg-exporter-{{< param version >}}-1.ppc64le.rpm)               |
| Tarball (Linux amd64)   | [pg_exporter-{{< param version >}}.linux-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.linux-amd64.tar.gz)     |
| Tarball (Linux arm64)   | [pg_exporter-{{< param version >}}.linux-arm64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.linux-arm64.tar.gz)     |
| Tarball (Linux ppc64le) | [pg_exporter-{{< param version >}}.linux-ppc64le.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.linux-ppc64le.tar.gz) |
| Tarball (macOS amd64)   | [pg_exporter-{{< param version >}}.darwin-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.darwin-amd64.tar.gz)   |
| Tarball (macOS arm64)   | [pg_exporter-{{< param version >}}.darwin-arm64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.darwin-arm64.tar.gz)   |
| Tarball (Windows amd64) | [pg_exporter-{{< param version >}}.windows-amd64.tar.gz](https://github.com/pgsty/pg_exporter/releases/download/v{{< param version >}}/pg_exporter-{{< param version >}}.windows-amd64.tar.gz) |

Install a downloaded RPM with `sudo dnf install ./<package>.rpm`, or a DEB with `sudo apt install ./<package>.deb`. For an archive, extract it and install the binary in your `$PATH`. Archives also include `pg_exporter.yml`, `package/pg_exporter.default`, `package/pg_exporter.service`, and `LICENSE`.

After installation, run `pg_exporter --version`. Package users can [start the systemd service](/deploy/#systemd-deployment-rpmdeb-packages). For an archive installation, prepare the monitoring credentials and use the [foreground example](/deploy/#process-settings).

> [!NOTE] RPM package rename
> Starting with `v1.4.1`, the official RPM package name and artifact prefix change from `pg_exporter` to `pg-exporter`, matching the DEB package and repository install commands. The new RPM also provides and obsoletes the legacy `pg_exporter` package name, allowing direct upgrades from earlier releases.

Download `checksums.txt` from the same release and verify files before installation. On Linux, run `sha256sum -c checksums.txt --ignore-missing` in the download directory; each downloaded artifact must report `OK`. On macOS, calculate `shasum -a 256 <file>` and compare its digest with the matching line in `checksums.txt`.

## Repository

The `pg-exporter` package is also available in the [`pigsty-infra`](https://ext.pgsty.com/repo/infra) repo.
You can add the repo to your system and install it with your OS package manager:

### YUM

For EL distributions such as RHEL, Rocky Linux, CentOS, AlmaLinux, and Oracle Linux:

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

For Debian, Ubuntu and compatible Linux Distributions:

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

The [official image](https://hub.docker.com/r/pgsty/pg_exporter) supports Linux amd64 and arm64. Pull the version you intend to deploy:

```bash
docker pull pgsty/pg_exporter:{{< param version >}}
docker run --rm pgsty/pg_exporter:{{< param version >}} --version
```

The image includes `/etc/pg_exporter.yml`. Mount a replacement there for custom collectors. Auto-discovery is already enabled; set `PG_EXPORTER_AUTO_DISCOVERY=false` to disable it.

Use the [Docker deployment example](/deploy/#docker-deployment) to mount the connection secret and start the container. The `scratch` image has no CA bundle; mount a CA file when using `sslmode=verify-ca` or `verify-full`.

## Build from Source

Check out the release tag and use the Go version declared by its `go.mod` (Go 1.26.5 or later for v1.4.1):

```bash
git clone --depth 1 --branch v{{< param version >}} https://github.com/pgsty/pg_exporter.git pg_exporter-src
cd pg_exporter-src
go build -ldflags='-X pg_exporter/exporter.Version=v{{< param version >}}' -o /tmp/pg_exporter .
/tmp/pg_exporter --version
sudo install -m 0755 /tmp/pg_exporter /usr/local/bin/pg_exporter
sudo install -m 0644 pg_exporter.yml /etc/pg_exporter.yml
```

This installs the binary at `/usr/local/bin/pg_exporter`. Use the [foreground example](/deploy/#process-settings) to run it. For a systemd service, use an RPM/DEB package; it configures the runtime account and a service unit that runs `/usr/bin/pg_exporter`.

## Compatibility

Use the default configuration for PostgreSQL 10 and later; it includes PostgreSQL 19 branches. PostgreSQL 9.1–9.6 needs the `legacy/pg_exporter.yml` file from the matching source tag. Binary release archives do not include this legacy file.

From the source checkout above:

```bash
pg_exporter --config=legacy/pg_exporter.yml --url='postgres://monitor@localhost:5432/postgres'
```

The bundled PgBouncer collectors require 1.8 or later. See [Compatibility](/compatibility/) for version selection, architectures, and collector prerequisites.
