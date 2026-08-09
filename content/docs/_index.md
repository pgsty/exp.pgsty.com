---
title: "PG Exporter Documentation"
linkTitle: "Docs"
description: "Install, deploy, secure, operate, and extend pg_exporter."
weight: 1
type: docs
icon: fa-solid fa-book
toc_root: true
---

`pg_exporter` is an advanced PostgreSQL and pgBouncer metrics exporter for Prometheus-compatible monitoring systems. It combines built-in availability and role metrics with a declarative SQL collector engine, so the metric surface can evolve independently of the Go binary.

These docs target the latest stable release, **[v{{< param version >}}](https://github.com/pgsty/pg_exporter/releases/tag/v{{< param version >}})**. They are maintained as a standalone, bilingual manual and are deliberately more detailed than the former Pigsty module pages.

## Start Here

| Guide | Use it when you need to… |
|:---|:---|
| [Introduction](/intro/) | Understand the architecture, execution model, and operational boundaries |
| [Getting Started](/start/) | Get a working exporter and Prometheus target in about ten minutes |
| [Installation](/install/) | Choose RPM, DEB, tarball, Docker, Pigsty, or source installation |
| [Compatibility](/compatibility/) | Check PostgreSQL, pgBouncer, OS, CPU, package, and container support |

## Run It in Production

| Guide | What it covers |
|:---|:---|
| [Production Deployment](/deploy/) | Flags, environment variables, systemd, Docker, Kubernetes, discovery, scraping, and alerting |
| [Security](/security/) | Least-privilege database access, secrets, TLS, HTTP authentication, and network exposure |
| [Troubleshooting](/troubleshooting/) | A symptom-driven runbook using logs, `/up`, `/explain`, `/stat`, and config validation |

## Understand and Extend It

| Reference | What it covers |
|:---|:---|
| [Collector Configuration](/config/) | The complete YAML schema: queries, tags, predicates, TTL, timeout, labels, counters, gauges, and snapshot histograms |
| [Bundled Collectors](/collectors/) | All 58 definition files, collector groups, prerequisites, cost, and cardinality considerations |
| [HTTP API](/api/) | Metrics, health, role-routing, reload, explain, statistics, version, and landing endpoints |
| [Development](/development/) | Build, test, change collectors, regenerate merged configs, and understand release artifacts |
| [Release Notes](/release/) | One bilingual article per tagged version, newest first |

## Documentation Contract

- Commands and paths are checked against the current `pg_exporter` source tree and the v{{< param version >}} release artifacts.
- Stable-release behavior is the default contract. Unreleased `main` behavior is called out explicitly when relevant.
- PostgreSQL 19 collector branches are included, but PostgreSQL's own release status still determines whether a target is suitable for production.
- The English and Simplified Chinese pages are paired; use the language switcher to move between equivalent pages.

For source code, issues, and contributions, visit [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter).
