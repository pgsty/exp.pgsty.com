---
title: "The PostgreSQL Observability Product We Chose Not to Build"
linkTitle: "Observability Product Pivot"
date: "2026-08-13T14:17:01+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "Why a separate incident workbench became a CSV log collector inside PG Exporter"
summary: "Superseded on 2026-08-24. CSV parsing and durable-state requirements became a bounded log-metrics feature; the separate product was dropped."
categories: [design]
tags: [Design, Product, PostgreSQL, Observability]
---

We first considered a local PostgreSQL incident workbench. It would read structured logs, reconstruct session timelines, provide interactive filters and a terminal interface, and later run as an agent.

> **Status:** Superseded on 2026-08-24 by [PostgreSQL log metrics](/design/postgres-log-metrics/).<br>
> **Decision date:** Research began on 2026-08-13; scope changed on 2026-08-24.<br>
> **Last verified:** 2026-10-13.<br>
> **Scope:** The separate PostgreSQL incident workbench and agent proposal.<br>
> **Delivery:** Stopped at proposal stage; never implemented, released, or deployed.

The immediate need was smaller: derive reliable operational metrics from PostgreSQL logs. We chose to add a background collector to PG Exporter. This record explains which findings survived and why the separate product was dropped.

## The original proposal {#original-hypothesis}

During an incident, a DBA may have local logs without a central log service. A tool that understands PostgreSQL CSV, SQLSTATE, sessions, and rotation could build a timeline without uploading SQL text.

The proposed workbench included:

- PostgreSQL 14+ CSV parsing, including multiline fields;
- filters for time, severity, SQLSTATE, database, user, application, and session;
- context across renamed log files;
- an interactive terminal interface;
- local processing and low-cardinality Prometheus metrics;
- a future daemon with durable cursors and multiple output destinations.

## Findings retained {#retained-findings}

PostgreSQL 14 through 18 document the same 26-column CSV layout. The sample import schema uses `(session_id, session_line_num)` as a primary key. CSV fields can contain commas, quotes, and newlines, so the parser must read complete records.

SQLSTATE is more stable than localized message text. It is the primary error classifier. Checkpoint, autovacuum, lock-wait, temporary-file, and connection messages need tested message patterns for the supported versions and language.

Raw SQL, user names, database names, client addresses, and session identifiers are unsuitable as default metric labels. They expose source data and make the number of series depend on workload. Fixed event categories and bounded distributions suit Prometheus.

Rotation, partial writes, restart recovery, and cursor persistence determine whether counts are reliable. They belong in the feature contract from the start.

## Why the scope changed {#rejected-product}

A workbench needs its own commands, output schema, interface, packages, documentation, and release cycle. An agent also needs queues, retries, retention rules, and service management. These responsibilities exceed those of a metrics exporter.

PG Exporter already provides a scrape target, `/metrics`, packaging, and Pigsty integration. Its development coordinator also provides component health. A bounded log collector can reuse those facilities and meet the immediate need.

We therefore stopped the separate product, repository, and branding work. Interactive investigation and log delivery were removed from the scope.

## Replacement {#replacement}

The decision on 2026-08-24 was:

> Add a default-off background PostgreSQL CSV log collector to PG Exporter. Publish a bounded set of operational metrics on the existing `/metrics` endpoint.

The replacement keeps complete CSV parsing, file identity, rotation and truncation handling, durable cursors and aggregates, atomic persistence, immutable snapshots, fixed labels, and explicit input-gap metrics.

Log shipping, interactive search, session timelines, arbitrary regular expressions, and automatic root-cause analysis remain outside its scope. The implementation contract is in [PostgreSQL log metrics](/design/postgres-log-metrics/).

## When to reconsider {#why-keep-it}

A separate workbench would need evidence of a local investigation workflow that existing log tools do not serve. It would also need users to validate the event model and maintainers to own its release and support cycle. Until those needs are established, PG Exporter will expose aggregate metrics.

## Sources {#sources}

The CSV requirements come from the official logging documentation for [PostgreSQL 14](https://www.postgresql.org/docs/14/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) and [PostgreSQL 18](https://www.postgresql.org/docs/18/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG). The replacement's source boundary and test evidence are recorded in its linked design article.
