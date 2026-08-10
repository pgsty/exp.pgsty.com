---
title: "Download PG Exporter"
linkTitle: "Download"
description: "Choose, install, configure, enable, and verify PG Exporter packages, archives, containers, Pigsty automation, or source builds"
weight: 25
icon: fa-solid fa-download
categories: [Guide]
---

PG Exporter {{< param version >}} is available as managed Linux packages, direct RPM/DEB files, release archives for Linux/macOS/Windows, a multi-architecture container image, Pigsty automation, and source. Choose by lifecycle ownership, not by feature set: every route runs the same exporter and declarative collectors.

{{% alert title="Product and artifact names" color="info" %}}
The product name is **PG Exporter**. The Linux package is `pg-exporter`; the executable, service, configuration file, and container repository retain the compatibility name `pg_exporter`.
{{% /alert %}}

{{< nav-cards cols="4" >}}
{{< nav-card title="Linux packages" link="#repository-packages" icon="fa-solid fa-box-archive" badge="Recommended" desc="APT/YUM lifecycle, systemd unit, merged config, and /etc/default/pg_exporter." />}}
{{< nav-card title="Release artifacts" link="#github-release-artifacts" icon="fa-solid fa-file-zipper" desc="Versioned RPM, DEB, and Linux/macOS/Windows archives with SHA256 checksums." />}}
{{< nav-card title="Container" link="#container-image" icon="fa-brands fa-docker" desc="Pinned amd64/arm64 image for Docker, Podman, Compose, or an orchestrator." />}}
{{< nav-card title="Pigsty or source" link="#pigsty" icon="fa-solid fa-code-branch" desc="A complete monitoring stack through Pigsty, or a tagged build you own end to end." />}}
{{< /nav-cards >}}

## Choose an installation path

| Method | Best fit | Lifecycle owner | Service integration |
|:---|:---|:---|:---|
| Pigsty APT/YUM repository | Long-lived Linux hosts | OS package manager | Included systemd unit and defaults |
| Direct RPM/DEB | Pinned or offline Linux promotion | Your artifact pipeline | Included systemd unit and defaults |
| Release archive | Minimal install, macOS/Windows, custom layout | You | Service examples included; manual wiring |
| Container image | Container platforms | Container runtime/orchestrator | Restart and secrets policy are yours |
| Pigsty | PostgreSQL plus a complete observability stack | Pigsty automation | Integrated with metrics, rules, and dashboards |
| Source | Development, auditing, custom builds | You | Manual |
{.full-width}

For long-running Linux services, start with the repository package. It gives upgrades, file ownership, `/etc/default/pg_exporter`, the merged collector configuration, and systemd behavior as one managed unit.

## Repository packages

The `pigsty-infra` repository publishes `pg-exporter` for common EL and Debian/Ubuntu platforms.

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

The repository examples match the current Pigsty package channel. If your supply-chain policy requires signed package metadata, promote a verified release artifact into your own repository instead of weakening that policy on production hosts.

### Configure and enable the service {#enable-service}

The package installs:

- `/usr/bin/pg_exporter` — executable;
- `/etc/pg_exporter.yml` — merged collector configuration, preserved on upgrades;
- `/etc/default/pg_exporter` — process environment and options, preserved on upgrades;
- `pg_exporter.service` — systemd unit running as the `prometheus` user.

Create the [monitoring database role](/start/#create-monitoring-user), then set its connection URL:

```bash
sudoedit /etc/default/pg_exporter

# Set this value in the file; prefer .pgpass or a secret file in production.
PG_EXPORTER_URL='postgres://monitor@127.0.0.1:5432/postgres?sslmode=disable'
```

Enable, start, and verify the service:

```bash
sudo systemctl enable --now pg_exporter
sudo systemctl status pg_exporter
journalctl -u pg_exporter -n 50 --no-pager

curl -fsS http://127.0.0.1:9630/up
curl -fsS http://127.0.0.1:9630/metrics | grep '^pg_up '
```

Use `sslmode=verify-full` plus an explicit CA for remote production targets. The [deployment guide](/deploy/#monitoring-user-and-credentials) covers `.pgpass`, `PG_EXPORTER_URL_FILE`, HTTP TLS/authentication, and network exposure.

## GitHub release artifacts

The [v{{< param version >}} release](https://github.com/pgsty/pg_exporter/releases/tag/v{{< param version >}}) contains RPM and DEB packages plus archives for Linux, macOS, and Windows. Linux supports amd64, arm64, and ppc64le; macOS supports amd64 and arm64; Windows provides amd64.

{{% tabpane text=true persist=header %}}
{{% tab header="DEB package" selected=true %}}
Choose `ARCH=amd64`, `arm64`, or `ppc64le` to match the release filename:

```bash
VERSION={{< param version >}}
ARCH=amd64
curl -fLO "https://github.com/pgsty/pg_exporter/releases/download/v${VERSION}/pg-exporter_${VERSION}-1_${ARCH}.deb"
sudo apt install "./pg-exporter_${VERSION}-1_${ARCH}.deb"
```

Continue with [service configuration](#enable-service).
{{% /tab %}}
{{% tab header="RPM package" %}}
`uname -m` returns the release architecture names `x86_64`, `aarch64`, or `ppc64le` on supported systems:

```bash
VERSION={{< param version >}}
ARCH=$(uname -m)
curl -fLO "https://github.com/pgsty/pg_exporter/releases/download/v${VERSION}/pg-exporter-${VERSION}-1.${ARCH}.rpm"
sudo dnf install "./pg-exporter-${VERSION}-1.${ARCH}.rpm"
```

Continue with [service configuration](#enable-service).
{{% /tab %}}
{{% tab header="Tar archive" %}}
Choose `OS=linux` or `darwin`; choose `ARCH=amd64`, `arm64`, or Linux `ppc64le`. Windows users download the `windows-amd64` archive and run `pg_exporter.exe` from their chosen directory.

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

Run it directly with `PG_EXPORTER_URL=... pg_exporter`, or adapt the included `package/pg_exporter.service` and `package/pg_exporter.default` examples to your paths.
{{% /tab %}}
{{% /tabpane %}}

### Verify the download

Every release includes `checksums.txt`. Verify the files before installing or promoting them:

```bash
VERSION={{< param version >}}
curl -fLO "https://github.com/pgsty/pg_exporter/releases/download/v${VERSION}/checksums.txt"
sha256sum -c checksums.txt --ignore-missing
```

On macOS, use `shasum -a 256 <archive>` and compare it with the matching entry in `checksums.txt`.

## Container image

The official [`pgsty/pg_exporter`](https://hub.docker.com/r/pgsty/pg_exporter) image publishes amd64 and arm64 manifests. Pin the release tag for reproducible deployments:

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

Mount a custom collector file only when you need one:

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

{{% alert title="Scratch image" color="warning" %}}
The image contains the static exporter, merged config, and license, but no shell or operating-system CA bundle. Mount the required CA explicitly when using `sslmode=verify-ca` or `verify-full`.
{{% /alert %}}

For Compose and Kubernetes examples, probes, secrets, and Prometheus wiring, continue to [Container and Kubernetes deployment](/deploy/#docker-deployment).

## Pigsty

[Pigsty](https://pigsty.io/) is the integrated route when you want PG Exporter together with a PostgreSQL distribution, Prometheus-compatible metrics storage, recording/alerting rules, and Grafana dashboards.

```bash
curl -fsSL https://repo.pigsty.io/get | bash
cd ~/pigsty
```

The bootstrap only obtains Pigsty; choose the appropriate inventory and deployment procedure before running it against any host. See the [Pigsty installation guide](https://pigsty.io/docs/setup/install/) and its existing PostgreSQL monitoring workflow.

## Build from source

Use the Go version declared by the tagged `go.mod`, then build the exact release source:

```bash
git clone https://github.com/pgsty/pg_exporter.git
cd pg_exporter
git checkout "v{{< param version >}}"
make build

./pg_exporter --version
PG_EXPORTER_URL='postgres://monitor@127.0.0.1:5432/postgres' ./pg_exporter --dry-run
```

For a manual Unix install:

```bash
sudo install -m 0755 pg_exporter /usr/local/bin/pg_exporter
sudo install -m 0644 pg_exporter.yml /etc/pg_exporter.yml
```

Source builds do not create a service account or register a system service. If you need package-grade ownership and service behavior, use the RPM/DEB route or reproduce those controls deliberately.

## Activation checklist

Installation is complete only when the target can be scraped:

1. Create a least-privilege [monitoring role](/start/#create-monitoring-user).
2. Provide the connection through `--url`, `PG_EXPORTER_URL`, `PGURL`, or `PG_EXPORTER_URL_FILE`.
3. Run `pg_exporter --dry-run` and inspect [`/explain`](/api/#get-explain).
4. Verify `/up` and confirm `pg_up 1` at `/metrics`.
5. Add the exporter to [Prometheus-compatible scraping](/start/#hook-into-prometheus).
6. For production, review [credentials, TLS, HTTP exposure, systemd/container restart policy, and probes](/deploy/).

Need the complete artifact matrix or PostgreSQL/PgBouncer compatibility details? Use the [Installation reference](/install/) and [Compatibility matrix](/compatibility/).
