---
title: "The PostgreSQL Observability Product We Chose Not to Build"
linkTitle: "Observability Product Pivot"
date: "2026-08-13T14:17:01+08:00"
lastmod: "2026-08-24T12:17:38+08:00"
authors: [Vonng]
description: "Why a local-first PostgreSQL incident workbench was explored, then replaced by a much smaller CSV-log metrics feature inside PG Exporter"
summary: "Superseded on 2026-08-24. The investigation established durable CSV and cardinality requirements, then rejected a new workbench, agent, repository, and brand in favor of bounded metrics inside PG Exporter."
categories: [design]
tags: [Design, Product, PostgreSQL, Observability]
---

> **Decision status:** Superseded on 2026-08-24 by the in-process PostgreSQL CSV log metrics decision.<br>
> **Research date:** 2026-08-13.<br>
> **What remains valid:** CSV framing, rotation, SQLSTATE, privacy, and bounded-cardinality findings.<br>
> **What no longer applies:** a new product, repository, binary, brand, interactive query tool, TUI, agent, or log-delivery pipeline.

Before PostgreSQL log metrics were scoped, we explored a much larger product: a local-first incident workbench that could inspect structured logs, reconstruct session timelines, offer interactive filters and a terminal UI, and eventually run as a node signal agent.

The exploration was useful precisely because the product was not built. It separated facts that belonged to any correct PostgreSQL log parser from ambitions that would have changed PG Exporter's product category and operating model.

## The original hypothesis {#original-hypothesis}

The user problem was credible. During an incident, a DBA often has local PostgreSQL logs but no prepared query in a central platform. A tool that understood PostgreSQL CSV records, SQLSTATE, sessions, rotation, and multi-line fields could produce a useful timeline without uploading SQL text or deploying a new backend.

The proposed workbench emphasized:

- correct PostgreSQL 14+ CSV parsing rather than line-oriented regular expressions;
- filters over time, severity, SQLSTATE, database, user, application, and session;
- cross-file context through rename rotation;
- a terminal-first workflow for machines without a web service;
- local privacy by default;
- low-cardinality Prometheus metrics derived from the same parser;
- a possible future daemon with durable cursors and multiple outputs.

This was a coherent product idea. It was also far larger than the immediate need.

## What the research established {#retained-findings}

Several conclusions survived the pivot.

PostgreSQL 14 through 18 document the same 26-field CSV layout, including `session_id`, `session_line_num`, `backend_type`, leader PID, and query ID. PostgreSQL's sample import table uses `(session_id, session_line_num)` as a primary key. CSV values may contain commas, quotes, and newlines, so a physical-line scanner is not a correct parser.

SQLSTATE is more stable than localized message text and is therefore the best first classifier for errors. Message grammars remain useful for bounded PostgreSQL events such as checkpoint, autovacuum, lock wait, temporary-file, and connection messages, but they must be versioned and tested.

Raw query text, detail, hint, context, user, database, application, client address, PID, session, transaction ID, and file path are unsafe default metric labels. Prometheus is a good destination for bounded counts and distributions, not a substitute for a log index.

Rotation, partial writes, restart recovery, and cursor persistence are product requirements, not parser implementation details. A tool that silently double-counts or skips bytes after restart produces worse evidence than no tool.

## Why the larger product was rejected {#rejected-product}

The decisive problem was not technical feasibility. It was scope and responsibility.

A workbench would require an independent command vocabulary, output schema, UX, packaging, documentation, support surface, and release lifecycle. A durable agent would add service management, upgrades, queues, backpressure, retry, disk retention, security policy, and delivery SLOs. A TUI and log index would optimize for investigation, while a Prometheus exporter optimizes for bounded machine-readable state. Treating all of them as one MVP would delay the smallest useful outcome and make its reliability harder to prove.

The new product also lacked a validated reason to exist separately. The immediate request was not “search every log” or “send logs to another backend”. It was “derive a small set of reliable operational metrics from PostgreSQL's structured log”. PG Exporter already owned the target identity, `/metrics`, packaging, component health, and Pigsty integration needed for that job.

Brand and repository work were therefore distractions. Naming a speculative product could make the architecture feel more committed than the user value. The design review chose to remove the entire public naming surface rather than polish it.

## The replacement decision {#replacement}

On 2026-08-24 the goal became deliberately smaller:

> Add one default-off background PostgreSQL CSV log collector to the existing PG Exporter process, and expose only bounded operational metrics on the existing `/metrics` endpoint.

The replacement excluded log shipping, OTLP, VictoriaLogs, Kafka, a web UI, TUI, full-text search, session timelines, arbitrary user regular expressions, automatic root-cause analysis, and other component logs.

It retained the hard parts that determine trust: complete CSV framing, file identity, rename and truncation handling, a durable cursor plus aggregates, atomic persistence, immutable snapshots, fixed labels, series limits, and explicit gaps.

The resulting engineering contract is documented in [Turning PostgreSQL CSV Logs into Durable Metrics](/design/postgres-log-metrics/).

## Why keep a superseded record {#why-keep-it}

Deleting the exploration would hide why apparently attractive features are absent. Publishing the raw research would be equally misleading: it contained a large naming exercise, market snapshots, and product recommendations that were intentionally overturned.

This calibrated record preserves the useful causal chain:

```text
credible incident workflow
    -> correct CSV and session research
    -> oversized workbench and agent proposal
    -> scope and ownership review
    -> bounded log metrics inside PG Exporter
```

Future maintainers should not reopen the larger product merely because interactive investigation sounds useful. Reconsider it only with evidence that users need a local query experience the existing log stack cannot provide, that more than one real consumer validates the event model, and that someone is prepared to own a separate product lifecycle.

## Sources {#sources}

The stable external facts retained here are grounded in PostgreSQL's own CSV log definitions for [PostgreSQL 14](https://www.postgresql.org/docs/14/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) and [PostgreSQL 18](https://www.postgresql.org/docs/18/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG). Product and branding snapshots from the original research are intentionally not reproduced.
