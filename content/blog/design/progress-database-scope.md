---
title: "Cluster Progress with Safe Relation Labels"
linkTitle: "Progress Database Scope"
date: "2026-11-09T00:00:00+08:00"
lastmod: "2026-11-09T00:00:00+08:00"
authors: [Vonng]
categories: [design]
tags: [Design, PostgreSQL, Compatibility]
summary: "v1.6.0: keep cluster-wide progress and use numeric OIDs for user relations in other databases."
---

> **Status:** Implemented in v1.6.0.<br>
> **Decision / last verification:** 2026-11-09.<br>
> **Scope:** v1.6.0 at source `6bee809` on main, [#115](https://github.com/pgsty/pg_exporter/issues/115); PostgreSQL 12+ vacuum, index creation, and cluster progress. Not shipped in v1.5.0.<br>
> **Delivery:** Source committed and pushed as `6bee809`; local validation and [Test Release](https://github.com/pgsty/pg_exporter/actions/runs/42549895870) passed. Versioned archives, RPM/DEB packages, and checksums are built for the draft. A public tag, public images, deployment, and production verification remain separate gates.

## Decision

The progress views report work across the instance, but `relid::regclass` resolves names only within the connected database. An OID from another database can resolve to an unrelated local relation.

Keep `pg_vacuuming`, `pg_indexing`, and `pg_clustering` tagged `cluster, primary`. Resolve `relname` as `relid::regclass::text` when the row belongs to the connected database or the relation is a system catalog: OIDs below 16384 (`FirstNormalObjectId`) are assigned by initdb and name the same catalog in every database. For other relations in another database, emit the numeric OID as text, retaining `datname` and `pid` to identify the task. Do not filter out cross-database rows.

Keep metric names, labels, types, version ranges, TTLs, and three cluster-level queries per refresh. Cross-database coverage continues when auto-discovery is disabled, a database is excluded, or the monitoring role cannot connect to it, subject to the progress view's existing visibility rules. No new connections or name lookups are required.

## Tradeoff and rejected alternatives

A numeric OID is less readable than a relation name, but accurately reports the identifier available from the main connection. This fixes false names without losing catalog names, such as a VACUUM of `pg_attribute` in another database; it deliberately does not promise cross-database name resolution for user relations.

Per-database collection was rejected because it increases refresh queries from three to three per monitored database, including when no progress exists. It also loses progress from excluded or inaccessible databases. Adding lookup connections for active tasks duplicates discovery and permissions handling. Renaming labels would require a separate metric migration. Base-backup progress is unchanged.

## Acceptance and upgrade

Execute the PostgreSQL 12–16, 17, and 18+ SQL variants with local and foreign rows sharing the same relation OID. Verify the local name, the foreign numeric OID, and the name of a foreign system catalog, with one sample per task. Check primary/replica planning, that discovered connections do not duplicate cluster collectors, and cross-database coverage with discovery disabled or excluded databases.

Update split YAML and generated configuration together. Existing installations must merge or replace these collector definitions; a binary-only upgrade does not apply this SQL correction. Local SQL tests do not establish production-load acceptance.

## Local verification

PostgreSQL 12, 17, and 18 passed monitoring-role SQL integration tests covering all three query-version branches. Temporary progress views include a local and foreign task with the same relation OID; the local task receives its name and the foreign task its numeric OID. A real PostgreSQL 18 index build remained visible once per metric with discovery disabled, with the database excluded, and when the monitoring role lacked CONNECT on that database. Planning tests cover PostgreSQL 12–19 and prevent duplicate collection on discovered connections.

A review follow-up added a foreign `pg_catalog.pg_attribute` row to the fixture. On PostgreSQL 18.6 it reports `pg_attribute`; the earlier condition reported `1249`. A live throttled VACUUM of `pg_attribute` in another database confirmed the same, while a user table there still reported its OID. PostgreSQL 12 and 17 were not rerun for this follow-up.
