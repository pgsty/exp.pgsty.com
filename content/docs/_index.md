---
title: "PG Exporter Documentation"
linkTitle: "Docs"
description: "Install, deploy, secure, operate, and extend pg_exporter."
weight: 1
type: docs
icon: fa-solid fa-book
toc_root: true
search_keywords: [pg_exporter, postgres exporter, PostgreSQL monitoring, PgBouncer, Prometheus, metrics]
search_boost: 1.6
---

PG Exporter collects PostgreSQL and PgBouncer metrics for Prometheus. These manuals describe **[v{{< param version >}}](https://github.com/pgsty/pg_exporter/releases/tag/v{{< param version >}})**.

## Start here {#start-here}

- [Introduction](/intro/) — How the exporter fits into your monitoring system.
- [Quick start](/start/) — Install the exporter and collect your first metrics.
- [Download](/download/) — Choose a package, binary archive, or container image.
{.cards}

## Run in production {#run-it-in-production}

- [Deployment](/deploy/) — Run a service and connect Prometheus.
- [Security](/security/) — Configure database permissions, credentials, and TLS.
- [Troubleshooting](/troubleshooting/) — Diagnose connection errors, missing metrics, and slow scrapes.
{.cards}

## Configure the exporter {#understand-and-extend-it}

- [Collector configuration](/config/) — Define SQL queries, metrics, and collection settings.
- [Bundled collectors](/collectors/) — Find available metrics and their prerequisites.
- [Command reference](/cmd/) — Look up flags, environment variables, and defaults.
- [HTTP API](/api/) — Check health, inspect collection, and reload configuration.
- [Compatibility](/compatibility/) — Check database versions, platforms, and architectures.
{.cards}

## Development and releases

- [Development](/development/) — Build the exporter, change collectors, and run tests.
- [Design records](/design/) — Read architecture decisions and plans for unreleased features.
- [Release notes](/release/) — Find changes and artifacts for each version.
{.cards}

Open search with {{< kbd "Ctrl" "K" >}} on Windows/Linux or {{< kbd "⌘" "K" >}} on macOS.

Source code and issues are at [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter).
