---
title: "Getting Started"
linkTitle: "Quick Start"
description: "Get PG Exporter running and expose PostgreSQL metrics to Prometheus in five minutes"
weight: 20
icon: fa-solid fa-rocket
categories: [Reference]
search_keywords: [quick start, install, monitoring user, pg_monitor, dry-run, pg_up, scrape, Prometheus, explain, stat]
search_boost: 1.5
layout: landing
landing: start
---

<!-- The landing layout renders `data/landing/start/<lang>.yaml`, not this body.
     The paragraph below is the page's searchable text: OINK's offline index
     skips a page with no raw content. -->

Install PG Exporter, create a least-privilege `pg_monitor` role on the target
PostgreSQL instance, point the exporter at it with `PG_EXPORTER_URL`, parse the
configuration with `pg_exporter --dry-run`, and start it on `:9630`. A scrape of
`/metrics` returning `pg_up 1`, `pg_version`, and `pg_in_recovery` means the
pipeline works; then add the target to a Prometheus scrape job whose interval
stays above the collector TTLs. When something is off, `/explain` reports each
collector's planning verdict and `/stat` reports its errors and durations.
