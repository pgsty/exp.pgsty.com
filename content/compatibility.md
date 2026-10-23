---
title: "Compatibility"
linkTitle: "Compatibility"
description: "Supported PostgreSQL and PgBouncer versions, release artifacts, architectures, and deployment constraints"
weight: 40
icon: fa-solid fa-layer-group
categories: [Reference]
---

Choose an artifact for the exporter host and a collector configuration for the database version. Then install any views or extensions required by the collectors you enable. This page describes the configuration shipped with v{{< param version >}}.

## Database Targets

| Target | Status | Configuration |
|:---|:---|:---|
| PostgreSQL 10-18 | Default support | `pg_exporter.yml` / `config/` |
| PostgreSQL 19 | Version-specific branches included | Default config; check queries against your server build |
| PostgreSQL 9.1-9.6 | Legacy support | `legacy/pg_exporter.yml` / `legacy/config/` |
| PostgreSQL 9.0 and older | Unsupported | — |
| PgBouncer 1.8+ | Version-specific collectors | `0910`-`0940` collector files; connect to the admin database |
{.full-width}

PostgreSQL 19 branches cover recovery, locks, autovacuum scores, WAL, subscriptions, receivers, and replication slots. Version selection uses the server version number; check `/stat` after the first scrape to find queries that need adjustment for your server build.

The bundled PgBouncer collectors require 1.8 or later. That version changed the `SHOW STATS` fields used by these queries. The latest configured branches have no upper version bound. When you upgrade PgBouncer, check collector results against the [upstream changelog](https://www.pgbouncer.org/changelog.html).

## Release Validation

The v1.5.0 candidate passed default primary collection as a non-superuser on PostgreSQL 9.1–9.6, 10–18, and 19 RC1, plus PgBouncer 1.26.1. PostgreSQL 10–13 used the documented subscription OID grant. Physical standby promotion, reconnect recovery, and concurrent scrape/health/reload requests were also tested. PostgreSQL 19 evidence refers to RC1, not an exhaustive check of every final-release build, extension, or production workload.

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

Release archives include the binary, merged default config, license, default environment file, and systemd unit. Get the PostgreSQL 9.x configuration from the matching source tag; it is not included in these binary archives. macOS and Windows artifacts are useful for development and remote targets; the packaged service integration is Linux-specific.

> [!NOTE] RPM name since v1.4.1
> The official RPM package and artifact prefix is `pg-exporter`. It declares `Provides` and `Obsoletes` for the former `pg_exporter` name, so direct upgrades remain possible. The executable and configuration names remain `pg_exporter` and `/etc/pg_exporter.yml`.

## Container Constraints

The official image is built from `scratch`. It contains the static exporter binary, `/etc/pg_exporter.yml`, and the license, but no shell and no operating-system CA bundle. Mount required CA certificates explicitly when using `sslmode=verify-ca` or `verify-full`.

## Collector-Level Requirements

Collector selection also depends on the target database:

- `primary` / `replica` tags restrict execution by recovery role.
- `dbname:`, `extension:`, `schema:`, and `username:` tags require matching facts.
- Predicate queries can perform additional runtime checks.
- Disabled-by-default collectors (`skip: true`) must be intentionally enabled.
- Auxiliary-view collectors such as table/index bloat require their views and privileges.

Scrape `/metrics` once, then use [`/explain`](/api/#get-explain) to inspect the current plan and `/stat` to check query results. [Bundled Collectors](/collectors/) lists the prerequisites for each file.
