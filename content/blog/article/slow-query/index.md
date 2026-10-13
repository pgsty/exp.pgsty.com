---
title: "Diagnose PostgreSQL slow queries"
date: 2021-02-23
authors: [vonng]
summary: >
  Use query statistics, logs, and monitoring to find a slow query, test its cause, and verify a fix.
tags: [PostgreSQL, PG Admin, Performance]
---

This walkthrough uses the Pigsty sandbox and dashboards from February 2021.

Slow queries occupy connections, hold locks, and consume CPU and I/O. On a standby, a long query can conflict with WAL replay. PostgreSQL can delay replay or cancel the conflicting query, depending on its standby settings. See [hot standby conflicts](https://www.postgresql.org/docs/current/hot-standby.html#HOT-STANDBY-CONFLICT).

Monitoring helps you find the affected query and compare its behavior before and after a change.

![CPU use before and after query optimization](slow-query-8.webp)

In this example, query optimization reduced CPU use from about 40% to 4%.

## Collect query statistics and logs

The `pg_stat_statements` extension groups similar statements. It records call counts, execution times, rows retrieved or affected, and I/O statistics. To enable it:

1. Add `pg_stat_statements` to `shared_preload_libraries`.
2. Restart PostgreSQL.
3. Run `CREATE EXTENSION pg_stat_statements` in the database where you will read the statistics.

A query ID identifies a normalized statement. It does not identify one execution or guarantee one execution plan. Column names vary by PostgreSQL version; use the matching [pg_stat_statements reference](https://www.postgresql.org/docs/current/pgstatstatements.html).

Use `log_min_duration_statement` to log statements whose duration reaches a threshold. These logs help explain individual slow executions. Choose the threshold for the workload: logging every statement increases log volume and collection overhead.

A cumulative average can hide a recent regression. Take repeated samples to compare response time, call rate, and I/O over the incident interval. A slow-query threshold should reflect the application's latency requirement. A frequent point lookup and an occasional batch query need different thresholds.

## Reproduce the problem in a sandbox

This experiment deliberately removes an index. Run it in a disposable `pgbench` database.

The historical Pigsty sandbox used `make ri`, `make ro`, and `make rw` to initialize and exercise the `pg-test` cluster. The following commands apply write and read loads through its service ports:

```bash
# Write load: 50 transactions per second
while true; do pgbench -nv -P1 -c20 --rate=50 -T10 postgres://test:test@pg-test:5433/test; done

# Read load: 1000 transactions per second
while true; do pgbench -nv -P1 -c40 --select-only --rate=1000 -T10 postgres://test:test@pg-test:5434/test; done
```

Run each load in its own terminal. On the primary, remove the primary key:

```sql
ALTER TABLE pgbench_accounts DROP CONSTRAINT pgbench_accounts_pkey;
```

The point lookup loses its index. In this test, average response time increased from about 1 ms to 300 ms. One replica's QPS fell from 500 to 7.

![Query rate and response time after removing the index](slow-query-1.jpg)

The cluster load also increased and triggered alerts.

![Cluster load during the slow-query incident](slow-query-2.png)

## Find the query

Open **PG Cluster** to identify the affected instance. In **PG Query**, look for statements whose response time and share of execution time increased.

In this example, query ID `-6041100154778468427` changed from about 17 μs to 280 ms, while its QPS fell from 500 to 7.

![Identify the slow statement in the query overview](slow-query-3.jpg)

Open **PG Query Detail** for this query ID to find the SQL:

```sql
SELECT abalance FROM pgbench_accounts WHERE aid = $1;
```

![Statement text in the query detail](slow-query-4.png)

## Test the cause

The statement retrieves one account by `aid`. In **PG Table Catalog**, check whether that column has an index. In **PG Table Detail**, compare index scans and sequential scans on `pgbench_accounts`.

In this experiment, index scans fell to zero and sequential scans increased after the primary key was removed. This supports the missing-index diagnosis.

![Index scans and sequential scans on pgbench_accounts](slow-query-5.png)

## Apply and verify the fix

Restore an index on `aid` in the sandbox:

```sql
CREATE UNIQUE INDEX ON pgbench_accounts (aid);
```

This restores the lookup path. It does not recreate the primary-key constraint removed earlier.

![Query response time and throughput after the fix](slow-query-6.png)

![Cluster load after the fix](slow-query-7.png)

Compare the same workload and time intervals before and after the change. Record query latency, throughput, and resource use. Stop the test load when the experiment is complete.
