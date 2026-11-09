---
title: "Bounded SQL Scrapes and Client Cancellation"
linkTitle: "Scrape Lifetime"
date: "2026-11-09T00:00:00+08:00"
lastmod: "2026-11-09T00:00:00+08:00"
authors: [Vonng]
categories: [design]
tags: [Design, Reliability]
summary: "v1.6.0: bounded waiting for two scrapers, request cancellation, and the existing failure-cache policy."
---

> **Status:** Implemented in v1.6.0.<br>
> **Decision / last verification:** 2026-11-09.<br>
> **Scope:** v1.6.0 at source `6bee809` on main, addressing [#116](https://github.com/pgsty/pg_exporter/issues/116). Not shipped in v1.5.0.<br>
> **Delivery:** Source committed and pushed as `6bee809`; local validation and [Test Release](https://github.com/pgsty/pg_exporter/actions/runs/42549895870) passed. Versioned archives, RPM/DEB packages, and checksums are built for the draft. A public tag, public images, deployment, and production verification remain separate gates.

## Decision

Queries previously derived their contexts from `context.Background()`, allowing work to continue after the metrics client disconnected. More HTTP requests could wait indefinitely for the exporter lock. Bound this work while preserving failure isolation and cache reuse.

Admit at most two metrics requests, including collection, waiting, and response writing. One request collects at a time; a second scraper can wait for the same collection lock within its remaining request budget. Further requests receive HTTP 503. Waiting is cancelable without starting another goroutine or executing SQL. This supports two Prometheus scrapers without an unbounded queue or shared cancellation ownership.

Derive the request budget from the existing 30-second HTTP write timeout, shortened by a valid positive finite `X-Prometheus-Scrape-Timeout-Seconds` header. Queueing consumes this same budget. Prechecks inherit the context; collection checks it before each database and collector and starts no further collector once it expires. A collector already running with a timeout finishes its predicates and main query, which share that one deadline, even if the request ends, and its result is cached normally for later scrapers. A negative query timeout removes the per-query deadline, so only such a query is canceled with the request.

Keep the existing failure-cache policy: a refresh that fails, including a canceled unbounded query, clears that collector's result and records its attempt for the normal TTL, so the next request does not immediately repeat it. A departing client never turns a healthy bounded refresh into a failure: a fatal collector does not report `pg_up 0` to other scrapers, and 60- or 300-second size and bloat collectors do not disappear for their TTL. A fatal collector with a negative timeout is the exception: canceling it caches a fatal failure for its TTL, so fatal collectors should keep a timeout. A pass ended by the client or the request budget has an INFO summary log and is not counted in `pg_exporter_scrape_error_count` or `pg_exporter_server_scrape_error_count`, which keep counting connection and fatal collector errors. Other collectors' caches remain intact. No partial result from the interrupted collector is published, and no expired value is silently served as fresh. TTL zero and `--disable-cache` still explicitly request refreshes on every scrape. A long TTL therefore also delays recovery from a failed refresh; this is the existing tradeoff, not a new retry scheduler.

After gathering produces the response snapshot, release the collection lock before encoding and writing. The request still occupies an admission slot until its response finishes, bounding both waiting and slow responses. Keep Prometheus encoding, compression, Go/process metrics, and handler instrumentation. The normal collector interface remains usable without storing request context on the exporter.

## Alternatives and boundaries

Immediate rejection of every overlapping request causes avoidable gaps for two scrapers. Clearing the retry timestamp on cancellation repeatedly runs expensive queries and churns connections. Both were rejected during review. Canceling bounded queries with the request was also rejected: one client's disconnect became a failure cached for every scraper, and each lib/pq cancellation closes its connection. Letting the running collector finish normally costs up to its own timeout (2 seconds in the default configuration) of collection-lock time after the budget expires. Stopping between that collector's predicates and main query was rejected: it needs a separate not-attempted state and rollback, while saving only work bounded by the same deadline. Serving old results indefinitely would conceal stale measurements and needs a separate freshness contract. Background refresh, shared gathers, a parallel scheduler, new flags, and driver migration are outside this correction.

The budget stops collection and cancels unbounded SQL. A running bounded collector can extend the response past the budget, normally by up to its own timeout. A stalled network can hold the driver longer, as in v1.5.0, so neither the budget nor a query timeout is a hard wall-clock limit, and no fixed encoding margin is reserved. The HTTP write deadline remains the transport limit. In particular, lib/pq connection handshakes need an appropriate DSN `connect_timeout`; a query context alone does not bound every network phase. See the [target-state record](/design/target-state-contracts/) for independent health probes.

## Error Accounting

An interrupted pass does not increment `pg_exporter_scrape_error_count` or `pg_exporter_server_scrape_error_count`; its summary log is INFO `interrupted`. Query errors and fatal-query ERROR logs remain observable. A real failure coinciding with request cancellation can therefore be omitted from these two pass counters. Without request cancellation, connection/precheck failures and fatal query failures, including their own timeouts, retain their error accounting. Non-fatal failures remain query-level errors.

## Acceptance

Verify repeated cancellation does not bypass TTL; healthy collectors and valid caches remain usable; retry resumes after TTL expiry. Exercise two overlapping scrapers, a canceled waiter, a full admission limit, cancellation of unbounded SQL, a client leaving during bounded SQL whose result must stay cached, an interrupted pass that must not increment error counters, and a slow response that must not hold the collection lock. Real PostgreSQL checks must confirm cancellation, bounded SQL attempts, and successful later scrapes. Validate PgBouncer separately. Local acceptance does not establish a release or production-load guarantee.

## Local verification

The full race suite and ten repeated runs of the focused concurrency tests passed. On PostgreSQL 18.6, a canceled refresh executed once during its TTL, while six following requests returned healthy metrics without repeating the failed SQL; expiry allowed a successful retry. Five rounds of two overlapping scrapers both returned HTTP 200, with one SQL refresh per round. Tests also cover canceled waiters, admission exhaustion, partial rows, predicate/precheck cancellation, and releasing the collection lock before a slow response finishes. No background refresh or stale-value fallback was added.

These cancellation runs predate a review adjustment that changes only queries with a positive timeout. Afterward, on PostgreSQL 18.6, a client leaving or a 0.3-second budget during a 0.8-second bounded query let that query finish; the expired budget returned 503 after 0.8 seconds, and the next scrape reused the result without executing it again. A 3-second unbounded query was canceled by PostgreSQL (SQLSTATE 57014) when the client left at 1.5 seconds, left no active backend, and stayed absent within its TTL. Before the adjustment, the same bounded query was canceled and disappeared for its TTL. A regression test confirms that a client leaving during a fatal collector no longer gives the next scraper `pg_up 0`.

A second review found that the running collector's later predicates and main query also continue after cancellation, and that interrupted passes incremented both error counters with an error log. The contract above now states the collector-level behavior, and interrupted passes are no longer counted. On PostgreSQL 18.6, a client leaving during a 0.8-second fatal bounded query previously left both counters at 1 with an error log; afterward both stayed at 0 and the pass was logged at info level, while the next scrape returned `pg_up 1` and the cached metric. Regression tests now use explicit synchronization instead of sleeps, and a real connection failure is still counted; the full suite passed 20 race-detector runs.
