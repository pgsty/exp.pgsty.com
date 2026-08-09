---
title: "Compatibility"
linkTitle: "Compatibility"
description: "Supported PostgreSQL and pgBouncer versions, release artifacts, architectures, and deployment constraints"
weight: 40
icon: fa-solid fa-layer-group
categories: [Reference]
---

Compatibility has three separate layers: the exporter binary must run on the host, the selected collector branch must match the target server, and optional SQL objects or extensions must exist. “The process starts” therefore does not prove that every collector is eligible.

## Database Targets

| Target | Status | Configuration |
|:---|:---|:---|
| PostgreSQL 10-18 | Default support | `pg_exporter.yml` / `config/` |
| PostgreSQL 19 | Collector branches included | Default config; validate against the current pre-release/final server build |
| PostgreSQL 9.1-9.6 | Legacy support | `legacy/pg_exporter.yml` / `legacy/config/` |
| PostgreSQL 9.0 and older | Unsupported | — |
| pgBouncer 1.8-1.25+ | Supported | `0910`-`0940` collector files; connect to the admin database |
{.full-width}

PostgreSQL 19-specific branches cover new recovery, lock, autovacuum-score, WAL, subscription, receiver, and slot fields. As of August 2026, PostgreSQL 19 is still in beta; the PostgreSQL project states that beta builds are for testing rather than production. Check the [current PostgreSQL beta status](https://www.postgresql.org/developer/beta/) before deploying a PG19 target.

pgBouncer support starts at 1.8 because that line provides the admin `SHOW` interface used by the collectors. Version-specific branches currently cover schemas through the 1.25 line; the official [pgBouncer changelog](https://www.pgbouncer.org/changelog.html) is the source of truth for upstream releases.

## v{{< param version >}} Release Artifacts

| Artifact | Operating system | Architectures |
|:---|:---|:---|
| Tarball | Linux | amd64, arm64, ppc64le |
| Tarball | macOS | amd64, arm64 |
| Tarball | Windows | amd64 |
| RPM | RHEL-compatible Linux | x86_64, aarch64, ppc64le |
| DEB | Debian/Ubuntu-compatible Linux | amd64, arm64, ppc64le |
| Docker image | Linux container | amd64, arm64 |
{.full-width}

Release archives include the binary, merged config, license, default environment file, and systemd unit. macOS and Windows artifacts are useful for development and remote targets; the packaged service integration is Linux-specific.

{{% alert title="RPM name since v1.4.1" color="info" %}}
The official RPM package and artifact prefix is `pg-exporter`. It declares `Provides` and `Obsoletes` for the former `pg_exporter` name, so direct upgrades remain possible. The executable and configuration names remain `pg_exporter` and `/etc/pg_exporter.yml`.
{{% /alert %}}

## Container Constraints

The official image is built from `scratch`. It contains the static exporter binary, `/etc/pg_exporter.yml`, and the license, but no shell and no operating-system CA bundle. Mount required CA certificates explicitly when using `sslmode=verify-ca` or `verify-full`.

## Collector-Level Requirements

Some collectors have narrower requirements even on a supported server:

- `primary` / `replica` tags restrict execution by recovery role.
- `dbname:`, `extension:`, `schema:`, and `username:` tags require matching facts.
- Predicate queries can perform additional runtime checks.
- Disabled-by-default collectors (`skip: true`) must be intentionally enabled.
- Auxiliary-view collectors such as table/index bloat require their views and privileges.

Use [`/explain`](/api/#get-explain) against the real target to see the exact plan; use [Bundled Collectors](/collectors/) for the prerequisites of each file.
