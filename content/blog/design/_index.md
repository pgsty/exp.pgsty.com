---
title: "Design Records"
linkTitle: "Design"
description: "Architecture decisions, rejected alternatives, and implementation contracts for PG Exporter"
weight: 20
icon: fa-solid fa-pen-ruler
sidebar_expanded: true
blog_index: list
outputs: [HTML, RSS, print, markdown]
images: [img/pg_exporter-design.webp]
cascade:
  outputs: [HTML, print, markdown]
  images: [img/pg_exporter-design.webp]
---

Design records explain PG Exporter’s architecture, alternatives, and tradeoffs. Each record states its status, source boundary, and last verification date.

Snapshot Histograms shipped in v1.4.0. [Replication collector corrections](/design/replication-collector-contracts/) and [target state contracts](/design/target-state-contracts/) shipped in v1.5.0. [Scrape lifetime](/design/scrape-lifetime/), [progress database scope](/design/progress-database-scope/), [container trust](/design/container-trust/), and the health-probe amendment to [target state contracts](/design/target-state-contracts/) shipped in v1.6.0. Composite mode, cached pgBackRest metrics, and PostgreSQL log metrics remain on the `snort` development branch and are not in stable v{{< param version >}}. The separate observability-product proposal was superseded.

Use the [manuals](/docs/) for stable-release procedures and the [release archive](/release/) for shipped changes.
