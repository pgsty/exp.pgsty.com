---
title: "Introduction"
linkTitle: "Introduction"
description: "How PG Exporter collects metrics and fits into a monitoring system"
weight: 10
icon: fa-solid fa-lightbulb
categories: [Concept]
---

PG Exporter reads PostgreSQL or PgBouncer statistics and exposes them as Prometheus metrics. Prometheus collects these metrics through HTTP and stores them for queries, dashboards, and alerts.

Each exporter process monitors one PostgreSQL instance or one PgBouncer instance. To monitor both, run two processes.

## How collection works

A collector is a SQL query with a YAML definition. The definition tells the exporter how to convert result columns into metrics and labels.

On the first scrape, the exporter selects collectors for the target's version, role, and installed extensions. PostgreSQL database discovery can add connections to other databases in the same instance.

When Prometheus requests `/metrics`, the exporter runs the selected queries and returns their metrics. A collector can cache its results for a configured time, called its TTL. Until that time expires, scrapes reuse the cached results.

The exporter provides the HTTP endpoint. Prometheus stores the history; Grafana or another dashboard tool displays it.

## What you can monitor

The bundled collectors cover activity, replication, WAL, locks, transactions, database objects, and selected extensions. They use PostgreSQL monitoring views and PgBouncer administration commands. [Bundled collectors](/collectors/) lists their metrics and required permissions.

The exporter also reports its own state. For example, `pg_up` reports whether the main database scrape completed without a fatal error. `pg_version` identifies the database version, and `pg_in_recovery` identifies its role.

## Customize collection

Start with the bundled configuration, [`pg_exporter.yml`](https://github.com/pgsty/pg_exporter/blob/v1.5.0/pg_exporter.yml). Add queries when you need more metrics. Each collector can have its own selection conditions, timeout, and cache TTL.

After you change the configuration, reload it through `/reload`. The exporter checks the new configuration before it replaces the current configuration. You do not need to compile or restart the program.

[Collector configuration](/config/) explains the YAML fields and gives examples.

## Check collection

Use `/explain` to see the selected collectors for the main database. Use `/stat` to see their query counts, error counts, and durations. The [HTTP API](/api/) also provides health checks and primary/replica endpoints.

For connection errors, missing metrics, or slow queries, follow [troubleshooting](/troubleshooting/).

## Versions and next steps

These manuals describe **v{{< param version >}}**. The default configuration contains PostgreSQL 10–19 and PgBouncer 1.8–1.25 branches. A separate legacy configuration covers PostgreSQL 9.1–9.6. See [compatibility](/compatibility/) for details.

The [Design archive](/design/) describes development features, including combined sources, pgBackRest metrics, and PostgreSQL log metrics. These features are not included in v{{< param version >}}.

Follow the [quick start](/start/) to collect your first metrics. For an existing service, use [production deployment](/deploy/).
