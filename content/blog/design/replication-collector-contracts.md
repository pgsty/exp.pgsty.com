---
title: "Correcting Replication Collector Identity and Semantics"
linkTitle: "Replication Collector Corrections"
date: "2026-10-22T00:00:00+08:00"
lastmod: "2026-10-23T00:00:00+08:00"
authors: [Vonng]
description: "Minimal corrections to subscription identity, receiver states, origin permissions, and relation counts"
summary: "Shipped in v1.5.0. Add database identity to subscriptions, correct receiver mappings, and clarify optional permissions and table/sequence counts."
categories: [design]
tags: [Design, PostgreSQL, Compatibility, Prometheus]
---

> **Status:** Shipped in v1.5.0.<br>
> **Decision date / last verified:** 2026-10-22 / 2026-10-23.<br>
> **Scope:** Collector corrections in pg_exporter `main` commit `d97ba38fc8390984df994b2f9ea58b43ecfc8b89`, based on `72f00a4fa4e6eb7524174f2122b3fe1e1d608db4`; PostgreSQL `REL_19_RC1` at `0b8bff042a997fe50fcd1c4c83b9ef1cc9ed8a89`, with focused PostgreSQL 9.6–18 checks. These corrections ship in v1.5.0 and are absent from v1.4.1.<br>
> **Delivery:** Source committed and pushed; tag v1.5.0 points to `18912540fe5edce0ed0ee81fac0d989738ecaa87`. CI and the release workflow passed; the GitHub Release, RPM/DEB packages, archives, and Docker images are published. This does not establish production deployment or production-load acceptance.

## Decisions

| Problem | Selected correction | Preserved behavior |
|:---|:---|:---|
| Equal subscription names in different databases produce duplicate samples | Add `datname` to every `pg_sub` version branch | Existing metric families, including `pg_sub_id`, cluster scope, worker filtering, and values |
| Receiver CASE expressions contain sender state names | Map the actual receiver dictionary and correct HELP | Existing valid codes 0, 4, and 5; unknown/NULL remains -1 |
| The optional origin collector's permission instructions are incomplete | Keep `skip: true`; document explicit user-managed grants and version limits | Original SQL, metrics, and default-off behavior |
| Publication and subscription relation counts describe different sets | Clarify HELP and manuals | SQL, labels, values, and absent-series behavior; no new sequence metric |

## Subscription identity

The pair `(datname, subname)` identifies a subscription within one PostgreSQL cluster. PostgreSQL enforces a unique `(subdbid, subname)` key, while database names are unique within the cluster. The query must resolve the owning database through the subscription OID:

```sql
JOIN pg_catalog.pg_subscription s ON s.oid = subscription_id
JOIN pg_catalog.pg_database d ON d.oid = s.subdbid
```

Here `subscription_id` means the existing source alias: `s2.subid` in the PG19 branch and the statistics-view subid in earlier branches. Add `d.datname` to the result and declare it as a LABEL. Do not use `CURRENT_DATABASE()`, join subscriptions by name alone, or add a constant connection-database label.

The existing query must still produce one row per subscription. Preserve the apply-leader filters and PG19's exclusion of sequence synchronization workers. Database identity distinguishes different subscriptions; worker filtering prevents repeated rows for the same subscription. Both are required.

### PostgreSQL 10–13 permission prerequisite

PostgreSQL 10–13 omitted public SELECT permission on `pg_subscription.oid`. The upstream correction was deliberately made for PostgreSQL 14, without changing older branches. Therefore this database-label design has an explicit upgrade prerequisite for those versions:

```sql
-- Execute as an administrator in the exporter's main connection database.
GRANT SELECT (oid) ON pg_catalog.pg_subscription TO monitor;
```

Use the actual monitoring role. The grant belongs in each database that may be used as the exporter's main connection, not merely the databases owning subscriptions. It grants no access to `subconninfo`. PostgreSQL 14+ needs no additional grant for this join under the standard catalog ACLs; locally tightened ACLs still require local provisioning.

This is a deployment cost, not an automatic permission repair. On PG10–13, apply the grant before deploying the modified collector configuration. Without it, SQL fails and the subscription metrics are absent even if the HTTP response itself remains 200. Acceptance must check expected samples and query errors as well as HTTP status.

### Alternatives and migration

An additional `subid` label would avoid both joins and the old-version permission prerequisite. Database identity was selected for readable, database-oriented filtering consistent with other collectors. Given that requirement, two catalog joins and one documented legacy grant are smaller than a new privilege wrapper or runtime fallback. Do not add both labels without a separate need.

Preserve the `id` GAUGE instead of converting it into a label and deleting `pg_sub_id`. Existing sample counts and family names remain unchanged, but the new label creates new time series. Check label-sensitive PromQL joins and aggregation. Database or subscription renames also change identity. Target labels continue to distinguish clusters.

## Receiver state dictionary

The receiver source was compared at release boundaries from PostgreSQL 9.6 through 19 RC1. PostgreSQL 9.6–18 has six states; PG19 adds `connecting`.

| Receiver string | Code | Availability |
|:---|---:|:---|
| streaming | 0 | PG9.6–19 |
| stopping | 4 | PG9.6–19 |
| connecting | 5 | PG19; unused in earlier servers |
| starting | 6 | PG9.6–19 |
| waiting | 7 | PG9.6–19 |
| restarting | 8 | PG9.6–19 |
| stopped | 9 | PG9.6–19 |
| other or NULL | -1 | All branches |

Remove `startup`, `catchup`, and `backup` from the receiver CASE and HELP. Reserve their old codes 1–3 rather than assigning new meanings. Apply the same mapping to the three current branches and the legacy `pg_recv_96` branch; no new version branch or Go state machinery is needed.

An internal state does not guarantee a visible statistics row. In RC1 the receiver function suppresses the row when the PID is zero or statistics are not ready. Do not fabricate a stopped or streaming sample when the row is absent. Preserve connecting behavior when sender host and port are NULL.

Adversarial testing also found that the legacy receiver query used `regexp_match()`, introduced in PostgreSQL 10, on PG9.6. Replacing its two first-capture expressions with scalar `substring(... FROM ...)` makes that query executable on PG9.6 without adding a branch, set-returning function, or conninfo parser. The regular expressions and resulting host/port labels stay the same. This narrow prerequisite is included with the dictionary correction.

PG9.6 itself reveals only the receiver PID to a non-superuser; the other statistics fields are NULL. The collector therefore reports state -1 under that role. Correcting SQL compatibility does not bypass this visibility rule or justify granting superuser to a monitoring account.

The final legacy query executed on PG9.6–12. A real PG9.6.24 standby returned streaming state 0 to its administrator, state -1 to the ordinary monitor, and 11 receiver samples with HTTP 200 to that monitor. Host/port fixtures covered missing fields, NULL, Unix paths, IPv6, repeated keys, and quoted input; PG10–12 produced the same results with the old and new extraction expressions. This preserves the existing regular-expression behavior, including its limitations on quoted values containing spaces.

## Optional replication origins

The current and legacy configurations already set `skip: true`. Keep that setting. Explain that users must provision privileges before explicitly enabling the collector.

For PostgreSQL 14+ with standard catalog ACLs, an administrator can grant the actual monitoring role:

```sql
GRANT SELECT ON pg_catalog.pg_replication_origin_status TO monitor;
GRANT EXECUTE ON FUNCTION
  pg_catalog.pg_show_replication_origin_status() TO monitor;
```

Run grants in the exporter's main connection database. PostgreSQL 13 and older retain an internal superuser check; GRANT alone does not enable direct non-superuser use. Keep those optional paths disabled unless the administrator separately chooses and owns an appropriate access arrangement. This correction adds no SECURITY DEFINER wrapper, automatic GRANT, retry under another identity, or synthetic zero values.

The origin catalog `pg_replication_origin` is already publicly readable under the standard ACLs, so an extra grant on it is redundant. Locally restricted catalog ACLs require the administrator to provision the query's catalog access as well.

## Publication and subscription counts

Document the exact existing behavior:

- `pg_pubrel_count` counts rows from `pg_get_publication_tables()`, not sequences. Its CROSS LATERAL query emits no row for empty or sequence-only publications; absence is not an explicit zero.
- In PG19, `pg_subrel_count` groups tables and sequences from `pg_subscription_rel` by synchronization state. The PG19 table states are i/d/f/s/r; sequence states are i/r.
- Counts on different sides are not a replication-health equality. Multiple publications, overlapping objects, partitions, refresh, and asynchronous synchronization can affect interpretation.

Change descriptions and manuals only. Keep `DISTINCT subid, subname` in the subscription relation query. Do not add `pg_pubseq_count`, a `relkind` label, zero-filling, or a different object-count definition in this patch.

## Validation and remaining gates

The final configuration and a binary built from the stated `main` baseline were tested with a non-superuser monitoring role against PostgreSQL 10.21, 11.16, 12.22, 13.23, 14.23, 15.18, 16.14, 17.10, 18.4, and 19 RC1. Two databases with the same subscription name produced distinct labels and zero duplicate sample keys. PG10–13 failed before the column grant, still failed when it was granted only in a subscription database, and passed after the grant in the main connection database; `subconninfo` remained inaccessible. The PG10–14 branches emitted 14 samples, PG15–18 emitted 18, and PG19 emitted 42, reflecting their existing family counts.

RC1 full-configuration checks passed for disabled and active subscriptions, automatic discovery on and off, and a physical standby. Targeted HTTP checks captured table-sync and sequence-sync workers before and after the scrape alongside apply workers, still producing only 42 subscription samples. The default full plan did not select `pg_origin`. Receiver mapping fixtures covered PG9.6 and each PG10–19 major; actual RC1 streaming and connecting were also observed, including connecting with NULL sender fields and HTTP state 5. Fixtures do not prove that every transient state was observed live.

Origin tests with real origin entries confirmed that the view grant alone is insufficient, PG14+ succeeds with the documented function grant, and PG13 and older still reject non-superusers. Empty origin catalogs are not a sufficient permission test: the LEFT JOIN may avoid calling the restricted function. On RC1 a mixed publication returned one table, its subscription counted one table plus one sequence, and empty/sequence-only publications emitted no row.

Local Go tests with the race detector, the compatibility HTTP-mux mode, `go vet`, dependency consistency, schema/version coverage, generated-file parity, and label-conflict checks passed. No Go implementation or dependency changes were needed. Source validation and the paired documentation build are separate from release and production acceptance.

## Implementation boundaries

The source change is limited to seven split collector files and their two generated bundles. The companion changes are the paired collector manuals and this paired Design record. The manuals distinguish existing permission/count semantics from the identity, dictionary, and PG9.6 SQL corrections in v1.5.0. Source review, commit, push, tagging, and formal artifacts are complete; production rollout remains a separate action.

Non-goals include a driver migration, Gatherer redesign, runtime privilege management, new collector branches, new metric families, changes to subscription relation aggregation, or unrelated legacy SQL repair.

## Primary references

- [RC1 subscription identity constraints](https://github.com/postgres/postgres/blob/0b8bff042a997fe50fcd1c4c83b9ef1cc9ed8a89/src/include/catalog/pg_subscription.h)
- [PG14 correction to subscription column permissions](https://github.com/postgres/postgres/commit/3590680b85a8e51ef8df550e5a10dedd0d2dfd88)
- [RC1 receiver state and visibility implementation](https://github.com/postgres/postgres/blob/0b8bff042a997fe50fcd1c4c83b9ef1cc9ed8a89/src/backend/replication/walreceiver.c)
- [PG14 origin function permission change](https://github.com/postgres/postgres/commit/cc072641d41c55c6aa24a331fc1f8029e0a8d799)
- [RC1 system views](https://github.com/postgres/postgres/blob/0b8bff042a997fe50fcd1c4c83b9ef1cc9ed8a89/src/backend/catalog/system_views.sql)
