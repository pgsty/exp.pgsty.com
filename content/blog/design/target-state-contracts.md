---
title: "Target Identity and Consistent Health Responses"
linkTitle: "Target State Contracts"
date: "2026-10-23T00:00:00+08:00"
lastmod: "2026-10-23T00:00:00+08:00"
authors: [Vonng]
categories: [design]
tags: [Design, PostgreSQL, Reliability]
summary: "Shipped in v1.5.0: validate connection URLs without disclosing credentials, preserve database identity, and publish coherent health responses."
---

> **Status:** Shipped in v1.5.0.<br>
> **Decision and last verification:** 2026-10-23.<br>
> **Scope:** v1.5.0 at source `1891254` (fix baseline `9b378cb`). This decision covers target URL handling and database identity, metadata-driven collector selection, HTTP health snapshots, YAML durations, and metrics-route validation.<br>
> **Delivery:** Source committed and pushed; tag v1.5.0 points to `18912540fe5edce0ed0ee81fac0d989738ecaa87`. CI and the release workflow passed; the GitHub Release, RPM/DEB packages, archives, and Docker images are published. This does not establish production deployment or production-load acceptance.

## Target identity

Malformed URL syntax and malformed query escaping must fail startup without printing the original URL or a parser error that contains it. The shared URL parser also rejects decoded query parameter names that are empty or contain Unicode whitespace or `=`. This prevents unsafe names from reaching driver parsing or bypassing password masking. Diagnostics use fixed text without the URL or offending name. Dropping an invalid query parameter can discard an explicit TLS setting. Omitted `sslmode` still defaults to `disable`; valid explicit settings remain intact.

Use the existing `lib/pq` parser to determine the database name for the supported URL forms, including paths, explicit query parameters, and database aliases. Reimplementing their precedence in exporter code can select PostgreSQL mode for a PgBouncer target or misidentify a discovered database. When replacing the database for discovery, remove both `dbname` and `database` query parameters and write one escaped path. Preserve all unrelated parameters and exact database-name characters. Service-file target resolution and PgBouncer identity inferred only from connection defaults remain outside this correction.

When `PG_EXPORTER_URL_FILE` is selected, empty or whitespace-only contents must fail startup. This is the file containing the connection URL; it is not a TLS private-key check.

## Collector selection

Successful metadata prechecks invalidate the query plan when username, schema membership, or extension membership changes, as they already do for version, database, and recovery state. Compare sets, not array order. The next collection rebuilds eligible collectors and their caches and resets query statistics through the existing planning path. Stable metadata retains the current plan and caches. This avoids requiring a manual reload after installing an extension without adding a poller or another metadata query.

## Health snapshots

Publish one atomic status enum: unknown, down, starting, primary, or replica. Derive `Up()` and `Recovery()` from that enum. Each health HTTP handler reads it once and derives both the response code and body from that value. Three separately atomic fields do not form one atomic snapshot, and repeated reads can combine different probe generations.

The existing routes, HTTP codes, background probe interval, and scrape-derived health updates remain. This guarantees internal response consistency; it does not make a cached probe a synchronous proof of database availability. A mutex is unnecessary because the entire state fits in one atomic integer.

## Metrics route

Startup validation must verify that a request for the configured path selects the metrics handler itself. A matching pattern string is insufficient: a mux redirect can report the same pattern without reaching that handler. Compare the returned handler with the registered metrics handler, reject paths that select a redirect or another endpoint, and retain escaped paths that reach metrics under the active mux. This does not require a blanket ban on percent-encoded paths.

## Validation and boundaries

Regression tests cover explicit database identity, special characters and conflicting parameters, malformed URLs, schema/extension/user eligibility changes, unchanged metadata ordering, concurrent health transitions, and reachable escaped paths and redirects under both HTTP mux implementations. New regression cases fail before the correction and pass afterward.

The final v1.5.0 pre-release checks add this evidence:

- Invalid TLS escaping is rejected before connecting; `verify-full` fails against a server without TLS. Logs omit connection passwords, and an empty selected URL file is rejected.
- Discovery with conflicting parameters and special characters returns the correct database samples. Adding and removing databases, schemas, and `hstore` changes the plan as metadata changes. Stable sets preserve caches.
- Invalid single-file reloads retain the previous definitions and caches. Health recovers after reconnecting. Physical standby promotion updates the role and tag selection. Concurrent scrape, health, and reload responses keep status codes and bodies consistent.
- Go race tests, both HTTP mux modes, `go vet`, Staticcheck, module and generated-config consistency, six target builds, RPM/DEB installation, and Docker builds pass. Short fuzz runs cover roughly 604,000 inputs, with valid UTF-8 URL identities and actual HTTP URL construction.
- Default primary collection was rerun as a non-superuser on PostgreSQL 9.1–9.6, 10–18, 19 RC1, plus PgBouncer 1.26.1. PostgreSQL 10–13 uses the documented subscription OID grant. This does not exhaust extension combinations, transient faults, or production workloads.

The full certificate-chain/hostname/mTLS matrix, a real SQLSTATE `57P03` startup transition, and production load are outside this verification scope. Docker certificate verification still requires a mounted CA. Directory loading can skip invalid files; empty YAML is a valid zero-collector configuration; `SIGTERM` does not wait for active HTTP requests. These existing behaviors are unchanged.

Related configuration validation rejects non-finite or positively overflowing YAML query TTL, query timeout, and predicate TTL seconds before conversion to `time.Duration`; zero/default and finite negative timeout semantics remain. No driver migration, optional-source integration, metric-name change, or general refactor is part of this decision.
