---
title: "PostgreSQL Macro Query Optimization with pg_stat_statements"
linkTitle: "PG Query Optimization: The Macro Way"
date: 2023-10-26
authors: [nikolay-samokhvalov]
summary: >
  Query optimization is one of the core responsibilities of DBAs. This article introduces how to use metrics provided by pg_stat_statements for macro-level PostgreSQL query optimization.
tags: [PostgreSQL, PG Admin, Performance]
---

This article describes the monitoring approach used in 2023. Its examples use PostgreSQL 15 fields and the dashboards available at that time.

Slow queries increase response times and consume database resources. They can also prolong lock contention and increase connection pressure. Query optimization is therefore a core DBA responsibility.

On the path of query optimization, there are two different approaches:

**Macro Optimization**: Analyze the overall workload, dissect and drill down, identifying and improving the worst-performing parts from top to bottom.

**Micro Optimization**: Analyze an individual query with its execution plan, slow query logs, and wait events.

Today we'll discuss the former. **Macro optimization** has three main goals and motivations:

**Reduce Resource Consumption**: Lower the risk of resource saturation, optimize CPU/memory/IO, typically using query **total time/total IO** as optimization targets.

**Improve User Experience**: The most common optimization goal, in OLTP systems typically using reduced **average query response time** as the optimization target.

**Balance Workload**: Ensure appropriate proportional relationships in resource usage/performance between different query groups.

These goals require query-level measurements. **pg_stat_statements** provides them.

![pgss-1.png](pgss-1.png)

-------------------

## Extension: PGSS

**pg_stat_statements**, hereafter abbreviated as **PGSS**, is the core tool for practicing the macro way.

PGSS comes from the official PostgreSQL Global Development Group, distributed as a first-party extension alongside the database kernel itself, providing methods for tracking SQL statement-level metrics.

I consider PGSS essential for production monitoring. At the time of writing, Pigsty loaded it by default alongside `auto_explain`, which supports analysis of individual query plans.

Add `pg_stat_statements` to `shared_preload_libraries` and restart PostgreSQL. Then run `CREATE EXTENSION pg_stat_statements` in the database where you want to query its views. PostgreSQL 15 also needs query IDs enabled; the default `compute_query_id = auto` meets this requirement.

PGSS groups statements by normalized query structure, database, user, and top-level status. A group can use different execution plans. The following table definition illustrates the PostgreSQL 15 view columns; create the extension rather than executing this definition.

```sql
CREATE TABLE pg_stat_statements
(
    userid                 OID,     -- (Label) User OID executing this statement
    dbid                   OID,     -- (Label) Database OID containing this statement
    toplevel               BOOL,    -- (Label) Whether this statement is top-level SQL
    queryid                BIGINT,  -- (Label) Query ID: hash of normalized query
    query                  TEXT,    -- (Label) Normalized query statement text
    plans                  BIGINT,  -- (Counter) Number of times this statement was planned
    total_plan_time        FLOAT,   -- (Counter) Total time spent planning this statement
    min_plan_time          FLOAT,   -- (Gauge) Minimum planning time
    max_plan_time          FLOAT,   -- (Gauge) Maximum planning time
    mean_plan_time         FLOAT,   -- (Gauge) Average planning time
    stddev_plan_time       FLOAT,   -- (Gauge) Standard deviation of planning time
    calls                  BIGINT,  -- (Counter) Number of times this statement was executed
    total_exec_time        FLOAT,   -- (Counter) Total time spent executing this statement
    min_exec_time          FLOAT,   -- (Gauge) Minimum execution time
    max_exec_time          FLOAT,   -- (Gauge) Maximum execution time
    mean_exec_time         FLOAT,   -- (Gauge) Average execution time
    stddev_exec_time       FLOAT,   -- (Gauge) Standard deviation of execution time
    rows                   BIGINT,  -- (Counter) Total rows retrieved or affected by this statement
    shared_blks_hit        BIGINT,  -- (Counter) Total shared buffer blocks hit
    shared_blks_read       BIGINT,  -- (Counter) Total shared buffer blocks read
    shared_blks_dirtied    BIGINT,  -- (Counter) Total shared buffer blocks dirtied
    shared_blks_written    BIGINT,  -- (Counter) Total shared buffer blocks written to disk
    local_blks_hit         BIGINT,  -- (Counter) Total local buffer blocks hit
    local_blks_read        BIGINT,  -- (Counter) Total local buffer blocks read
    local_blks_dirtied     BIGINT,  -- (Counter) Total local buffer blocks dirtied
    local_blks_written     BIGINT,  -- (Counter) Total local buffer blocks written to disk
    temp_blks_read         BIGINT,  -- (Counter) Total temp buffer blocks read
    temp_blks_written      BIGINT,  -- (Counter) Total temp buffer blocks written to disk
    blk_read_time          FLOAT,   -- (Counter) Total time spent reading blocks
    blk_write_time         FLOAT,   -- (Counter) Total time spent writing blocks
    temp_blk_read_time     FLOAT,   -- (Counter) Total time reading temporary blocks
    temp_blk_write_time    FLOAT,   -- (Counter) Total time writing temporary blocks
    wal_records            BIGINT,  -- (Counter) Total WAL records generated
    wal_fpi                BIGINT,  -- (Counter) Total WAL full page images generated
    wal_bytes              NUMERIC, -- (Counter) Total WAL bytes generated
    jit_functions          BIGINT,  -- (Counter) Number of functions JIT-compiled
    jit_generation_time    FLOAT,   -- (Counter) Total time spent generating JIT code
    jit_inlining_count     BIGINT,  -- (Counter) Number of times functions were inlined
    jit_inlining_time      FLOAT,   -- (Counter) Total time spent inlining functions
    jit_optimization_count BIGINT,  -- (Counter) Number of times queries were JIT-optimized
    jit_optimization_time  FLOAT,   -- (Counter) Total time spent on JIT optimization
    jit_emission_count     BIGINT,  -- (Counter) Number of times code was JIT-emitted
    jit_emission_time      FLOAT,   -- (Counter) Total time spent on JIT emission
    PRIMARY KEY (userid, dbid, queryid, toplevel)
);
```

PostgreSQL 15 view columns. All time fields use milliseconds. The `pg_query_exec_time` metric used below converts execution time to seconds. I/O timing requires `track_io_timing`; planning statistics require `pg_stat_statements.track_planning`.

Execution statistics are updated when a statement finishes successfully. Use `pg_stat_activity` for running statements and logs for errors. If planning succeeds but execution fails, PGSS can still record the planning statistics.

`queryid` depends on the parsed query and referenced database objects. Physical replicas normally produce matching IDs. Do not use it as a permanent identifier across PostgreSQL major versions, logical replicas, or dropped and recreated objects.

-------------------

## Raw Data

Columns in the **PGSS** view can be divided into three categories:

**Descriptive Label Columns**: Query ID (queryid), database ID (dbid), user (userid), a top-level query marker, and normalized query text (query).

**Measurement Metrics (Gauge)**: Eight statistics related to minimum, maximum, mean, and standard deviation, prefixed with min, max, mean, stddev and suffixed with plan_time and exec_time.

**Cumulative Metrics (Counter)**: **Other metrics** besides the above eight columns and label columns, such as calls, rows, etc. The most important and useful metrics are in this category.

First, let's explain queryid: queryid is a hash value generated from the normalized query after parsing the query statement and stripping constants, so it can be used to identify **the same type of query**. Different query statements may have the same queryid (same structure after normalization), and the same query statement may have different queryids (e.g., due to different search_path, resulting in different actual tables being queried).

The same query may be executed by different users in different databases. Therefore, in the PGSS view, the four label columns queryid, dbid, userid, toplevel together form the "primary key" that uniquely identifies a record.

For metric columns, **measurement-type metrics (GAUGE)** are mainly the eight statistics related to execution time and planning time, but users have no good way to control the statistical range of these statistics, so their practical value is limited.

The really important metrics are **cumulative metrics (Counter)**, such as:

**calls**: How many times this query group was invoked.

**total_exec_time** + **total_plan_time**: Total time consumed by the query group.

**rows**: Total rows retrieved or affected by the query group.

**shared_blks_hit** + **shared_blks_read**: Total buffer pool hits and read operations.

**wal_bytes**: Total WAL bytes generated by queries in this group.

**blk_read_time** and **blk_write_time**: Total time spent on block read/write IO

Here, the most meaningful metrics are **calls** and **total_exec_time**, which can be used to calculate the core metrics **QPS** (throughput) and **RT** (latency/response time) for query groups, though other metrics also have reference value.

![pgss-2.png](pgss-2.png)

Visualizing a query group snapshot from the PGSS view

Compare at least two snapshots to measure activity over an interval. Match the same query-group key and account for counter resets or evicted entries before calculating differences.

A single snapshot describes accumulated work since that entry began collecting statistics. Interval differences are more useful for investigating a particular incident.

![pgss-3.png](pgss-3.png)

> Calculating historical time-series metrics from multiple PGSS query group snapshots

The Pigsty deployment illustrated here took snapshots every 10 seconds of the top 256 queries by total time. With repeated samples of a cumulative metric M, we can calculate three derived metrics:

**dM/dt**: Derivative of metric M with respect to time, i.e., increment per second.

**dM/dc**: Derivative of metric M with respect to call count, i.e., average increment per call.

**%M**: Percentage of metric M in the overall workload.

These three types of metrics correspond exactly to the three types of macro optimization goals. The time derivative **dM/dt** reveals **resource usage per second**, typically used for resource consumption reduction optimization goals. The call count derivative **dM/dc** reveals **resource usage per call**, typically used for user experience improvement optimization goals. The percentage metric **%M** shows the percentage a query group occupies in the overall workload, typically used for workload balancing optimization goals.

-------------------

## Time Derivatives

Let's first look at the first type of metrics: time derivatives. Here, the metrics M we can use include: calls, total_exec_time, rows, wal_bytes, shared_blks_hit + shared_blks_read, and blk_read_time + blk_write_time. Other metrics also have reference value, but let's start with the most important ones.

![pgss-4.png](pgss-4.png)

> Visualizing time derivative metrics dM/dt

Calculating these metrics is actually quite simple, we just need to:

- First calculate the difference in metric value M between two snapshots: **M2 - M1**
- Then calculate the time difference between two snapshots: **t2 - t1**
- Finally calculate **(M2 - M1) / (t2 - t1)**

Production environments typically use data sampling intervals like 5s, 10s, 15s, 30s, 60s. For load analysis, we typically use 1m, 5m, 15m as common analysis window sizes.

For example, when we calculate QPS, we would calculate QPS for the last 1 minute, 5 minutes, and 15 minutes respectively. Longer windows provide smoother curves that better reflect long-term trends, but hide short-term fluctuation details and are not conducive to discovering momentary anomalies, so metrics of different granularities need to be viewed together.

![pgss-5.png](pgss-5.png)

> Showing QPS for a specific query group in 1/5/15 minute windows

For example, `rate(pg_query_calls{}[1m])` calculates the one-minute QPS rate for each collected query-group series. To calculate a total, select the intended instance and sum its series.

**QPS**

When M is calls, the result of time differentiation is QPS, with units of queries per second (req/s). This is a very fundamental metric. Query QPS is a throughput metric that directly reflects the load situation imposed by business. If a query's throughput is too high (e.g., 10000+) or too low (e.g., 1-), it may be worth attention.

![pgss-6.png](pgss-6.png)

> QPS: 1/5/15 minute µ/CV, ±1/3σ distribution

If we sum up all query groups' QPS metrics (without exceeding PGSS collection range), we get the so-called "global QPS." Another way to obtain global QPS is through client-side instrumentation, collection at connection pool middleware like PgBouncer, or using eBPF probes. But none are as convenient as PGSS.

Note that QPS metrics don't have load-wise **horizontal comparability**. Different query groups may have the same QPS but vastly different per-query execution times. Even the same query group may produce dramatically different load levels at different times due to different execution plans. Execution time per second is a better metric for measuring load.

**Execution Time Per Second**

When M is total_exec_time (+ total_plan_time, optional), we get one of the most important metrics in macro optimization: execution time spent on query groups. Interestingly, this derivative has units of seconds/per second, so the numerator and denominator cancel out, making it actually a dimensionless metric.

For example, 2 s/s means that this query group accumulated two seconds of server execution time per second. Concurrent backends can produce this value even on one CPU core: elapsed execution time includes waits.

![pgss-7.png](pgss-7.png)

> Execution time per second: 1/5/15 minute averages

Therefore, this value can also be understood as a percentage: it can exceed 100%, and in this perspective, it's a metric similar to host load1, load5, load15, revealing the **load level** generated by this query group. If divided by CPU core count, you can even get a normalized query load contribution metric.

However, we need to note that execution time includes time waiting for locks and I/O. So it's possible that query execution time is very long but has no impact on CPU load. For precise slow query analysis, we need to refer to **wait events** for further analysis.

**Rows Per Second**

When M is `rows`, the result is rows retrieved or affected per second. For a SELECT group, 10,000 rows/s describes the result-row rate. For an UPDATE or DELETE group, it describes affected rows, not data sent to clients.

![pgss-8.png](pgss-8.png)

> Rows retrieved or affected per second: 1/5/15 minute averages

**Shared Buffer Access Bandwidth**

When M is shared_blks_hit + shared_blks_read, we get the number of shared buffer blocks hit/read per second. If we multiply this by the default block size of 8KiB (rarely other sizes like 32KiB), we get the bandwidth of a query type "accessing" memory/disk: bytes per second.

For example, if a certain query type accesses 500,000 shared buffers per second, that's 3.8 GiB/s of internal access data flow: this is significant load and might be a good optimization candidate. Perhaps you should examine this query to see if it deserves this "resource consumption."

![pgss-9.png](pgss-9.png)

> Shared buffer access bandwidth and buffer hit rate

Another valuable derived metric is buffer hit rate: hit / (hit + read). It can be used to analyze possible causes of performance changes — cache misses. Of course, repeatedly accessing the same blocks in the shared buffer pool doesn't actually re-read, and even real reads might be from memory's FS Cache rather than disk. So this is just a reference value, but it's indeed a very important macro query optimization reference metric.

**WAL Volume**

When M is wal_bytes, we get the rate at which this query generates WAL, with units of bytes per second (B/s). This metric was introduced in PostgreSQL 13 and can quantitatively reveal the WAL size generated by queries: the more and faster WAL is written, the greater the pressure on disk flushing, physical/logical replication, and log archiving.

A typical example is: `BEGIN; DELETE FROM xxx; ROLLBACK;`. Such transactions delete lots of data, generate large amounts of WAL but perform no useful work. This metric can identify them.

![pgss-10.png](pgss-10.png)

> WAL byte rate: 1/5/15 minute averages

The DELETE completes successfully before the explicit ROLLBACK undoes its transaction. PGSS records the successful statement, including the WAL it generated.

SELECT can also generate WAL when it sets hint bits. With data checksums or `wal_log_hints` enabled, the first such change to a page after a checkpoint can require a full-page image. See the [WAL settings](https://www.postgresql.org/docs/15/runtime-config-wal.html#GUC-WAL-LOG-HINTS).

Check `wal_fpi` to determine whether full-page images explain WAL generated by a read-heavy workload.

![pgss-11.png](pgss-11.png)

> Shared buffer dirty/writeback bandwidth

For versions below 13, shared buffer dirty/writeback bandwidth metrics can serve as an approximate lower substitute for analyzing query group write load characteristics.

**I/O Time**

When M is `blk_read_time + blk_write_time`, convert milliseconds to seconds before taking the rate. The result is I/O time in seconds per second. Enable `track_io_timing` to collect these fields.

> I/O time is very helpful for analyzing query spike causes

These timings include reads satisfied by the operating-system cache. Compare them with host disk metrics to distinguish cached reads from storage I/O.

**Time derivative metrics** **dM/dt** can show the overall workload inside a database instance/cluster, especially useful for resource usage optimization scenarios. But if your optimization goal is improving user experience, then another group of metrics — **call count derivatives dM/dc** — might be more meaningful.

-------------------

## Call Count Derivatives

For **dM/dc**, the denominator changes from elapsed time to the **increase in call count**. This gives average resource use per completed call.

This class of metrics is even more important than the former because it provides several core metrics directly related to user experience, such as the most important — **query response time (RT, Response Time)**, or **latency**.

Calculating these metrics is also simple, we just need to:

- Calculate the difference in metric value M between two snapshots: **M2 - M1**
- Then calculate the difference in calls between two snapshots: **c2 - c1**
- Then calculate **(M2 - M1) / (c2 - c1)**

For PromQL implementation, **call count derivative metrics dM/dc** can be calculated using "**time derivative metrics dM/dt**". For example, to calculate RT, you can use **execution time per second** **/** **queries per second**, dividing the two metrics:

```promql
rate(pg_query_exec_time{}[1m]) / rate(pg_query_calls{}[1m])
```

![pgss-12.png](pgss-12.png)

> dM/dt can be used to calculate dM/dc

**Call Count**

When M is calls, differentiating with respect to itself is meaningless (result will always be 1).

**Average Latency/Response Time/RT**

Dividing the increase in `total_exec_time` by the increase in `calls` gives mean server execution time per call. Raw PGSS values produce milliseconds; the PromQL example above uses seconds. This is one part of client response time. Client-side measurements also include queueing, network, and application delays. Add planning time separately when planning statistics are enabled.

![pgss-13.png](pgss-13.png)

> RT: 1/5/15 minute µ/CV, ±1/3σ distribution

The mean covers successful completed executions represented by the collected entries. `pg_stat_statements.max` limits how many groups PGSS retains. Check this coverage when comparing workloads.

Client instrumentation measures response time at the application boundary. PgBouncer and PostgreSQL 14+ also provide database-level timing aggregates. PGSS adds query-group detail.

![pgss-14.png](pgss-14.png)

> RT: Statement-level/Connection pool-level/Database-level

Compare RT for the same query group under similar conditions. If its usual mean is below 1 ms, a rise above 10 ms warrants investigation.

When failures occur, RT views are also helpful for pinpointing causes: if all queries' overall RT slows down, it's most likely related to resource insufficiency. If only specific query groups' RT changes, it's more likely caused by slow queries and should be investigated further. If RT changes coincide with application deployments, consider whether to rollback those deployments.

Additionally, in performance analysis, stress testing, and benchmarking, **RT is also the most important metric**. You can evaluate system performance by comparing typical queries' latency performance in different environments (e.g., different PG major versions, different hardware, different configuration parameters) and continuously adjust and improve system performance based on this.

The mean and standard deviation of a sampled RT series show how interval averages vary. A percentile of those averages is not the P95 or P99 of individual query durations. Request-level percentiles require individual observations or a duration histogram.

RT is a useful measure of OLTP performance, alongside throughput and resource use.

**Average Rows Per Call**

When M is `rows`, the result is average rows retrieved or affected per call. For a point SELECT, this is usually a small result set; for a write statement, it is the number of affected rows.

![pgss-15.png](pgss-15.png)

> Point queries by primary key, average returned rows stable at 1

If a query group returns hundreds or even thousands of rows to clients per query, it should be examined. If this is intentional design, such as batch loading tasks/data dumps, then no action is needed. If these are requests initiated by applications/clients, there might be errors, such as statements lacking LIMIT restrictions or queries lacking pagination design. Such queries should be adjusted and fixed.

**Average Shared Buffer Read/Hit**

For `shared_blks_hit + shared_blks_read`, dM/dc gives shared-buffer accesses per query. Multiply by the block size, normally 8 KiB, to obtain bytes accessed per query (B/query). Repeated accesses count each time.

![pgss-16.png](pgss-16.png)

> Average shared-buffer bytes accessed per query

Query average accessed data volume usually matches average returned rows. If your query only returns a few rows on average but accesses gigabytes of data blocks, you need special attention: such queries are very sensitive to data hot/cold states. If all blocks are in the buffer, performance might be acceptable, but if starting from disk cold, execution time might change dramatically.

A PostgreSQL buffer miss can still be satisfied by the operating-system cache. Compare host metrics, the `pg_stat_kcache` extension, or PostgreSQL 16's `pg_stat_io` view to understand the underlying I/O.

Another pattern worth attention is sudden changes in this metric, which usually means this query group's **execution plan might have flipped/degraded**, very worthy of attention and further study.

**Average WAL Volume**

When M is wal_bytes, we get the average WAL size generated per query. This is a field newly introduced in PostgreSQL 13. This metric can measure query change footprint size and calculate read/write ratios and other important evaluation parameters.

![pgss-17.png](pgss-17.png)

> Stable QPS but periodic WAL fluctuations, inferred to be FPI influence

Another use is checkpoint optimization: if you observe periodic fluctuations in this metric (period approximately equal to checkpoint_timeout), you can optimize the amount of WAL generated by queries by adjusting checkpoint intervals.

**dM/dc** describes the average cost of one call. Use it to assess a query change, then check the workload totals to measure the overall effect.

**dM/dc** metrics like these provide important absolute value metrics, but to find which queries have the greatest potential optimization benefits, you need **%M percentage metrics**.

-------------------

## Percentage Metrics

Now let's study the third type of metrics: **percentage metrics**. That is, the proportion a certain query group occupies relative to the overall workload.

**Percentage metrics M%** provide us with the proportion of a certain query group relative to the overall workload, helping us identify "major players" in frequency, time, I/O time/count, find query groups with the greatest potential optimization benefits, and serve as important basis for priority assessment.

![pgss-18.png](pgss-18.png)

Common percentage metrics %M overview

A query group at 1,000 QPS might account for only 3% of calls, or more than 50%. If many of those calls are redundant, removing them can reduce database work. For expensive queries, compare their share of execution time or I/O as well as their share of calls.

A common optimization strategy is: first sort all query groups by the important metrics mentioned above: calls, total_exec_time, rows, wal_bytes, shared_blks_hit + shared_blks_read, and blk_read_time + blk_write_time **dM/dt** values over a period of time, take TopN (say N=10 or more), and add them to the optimization candidate list.

![pgss-19.png](pgss-19.png)

> Selecting TopSQL for optimization by specific criteria

Then, for each query group in the optimization candidate list, analyze their **dM/dc** metrics in turn, combined with specific query statements and slow query logs/wait events for analysis, decide whether this is a query worth optimizing. For queries decided (Plan) to optimize, you can use techniques introduced in the subsequent **"micro optimization"** article for tuning (Do), and use monitoring systems to evaluate optimization effects (Check), summarize and analyze before entering the next PDCA Deming cycle, continuing management optimization.

Besides taking TopN on metrics, visualization can also be used. Visualization greatly helps identify "major contributors" from workloads. Complex judgment algorithms might not match human DBAs' intuition for monitoring pattern recognition. To form a sense of proportion, we can use pie charts, tree maps, or stacked time series charts.

![pgss-20.png](pgss-20.png)

Stacking QPS of all query groups

For example, we can use pie charts to identify queries with the highest time consumption/IO usage in the past hour, use 2D tree maps (size represents total time consumption, color represents average RT) to show an additional dimension, and use stacked time series charts to show how proportions change over time.

We can also directly analyze current PGSS snapshots, sort by different concerns, and select queries to be optimized according to your own criteria.

![pgss-21.png](pgss-21.png)

I/O time is very helpful for analyzing query spike causes

-------------------

## Summary

Finally, let's summarize the content above.

PGSS provides rich metrics, among which the most important cumulative metrics can be processed in three ways:

**dM/dt**: Derivative of metric M with respect to time, revealing **resource usage per second**, typically used for resource consumption reduction optimization goals.

**dM/dc**: Derivative of metric M with respect to call count, revealing **resource usage per call**, typically used for user experience improvement optimization goals.

**%M**: Percentage metrics show the percentage a query group occupies in the overall workload, typically used for workload balancing optimization goals.

Usually, we select high-value candidate optimization queries based on **%M**: percentage metric Top queries, and use **dM/dt** and **dM/dc** metrics for further evaluation, confirming whether there's optimization space and feasibility, and evaluating post-optimization effects. This cycles continuously.

After understanding macro optimization methodology, we can use this approach to locate and optimize slow queries. Here's a specific example of [Using Monitoring Systems to Diagnose PG Slow Queries](/article/slow-query/). In the next article, we'll introduce experience and techniques for PostgreSQL query **micro optimization**.

-------------------

## References

`[1]` [PostgreSQL HowTO: pg_stat_statements](https://gitlab.com/postgres-ai/postgresql-consulting/postgres-howtos/) by Nikolay Samokhvalov

`[2]` [pg_stat_statements](https://www.postgresql.org/docs/15/pgstatstatements.html)

`[3]` [Using Monitoring Systems to Diagnose PG Slow Queries](/article/slow-query/)

`[4]` [How to Monitor Existing PostgreSQL (RDS/PolarDB/Self-built) with Pigsty?](/article/monitor-existing-pg/)

`[5]` [Pigsty v2.5 Released: Ubuntu/Debian Support and Monitoring Redesign/New Extensions](http://mp.weixin.qq.com/s?__biz=MzU5ODAyNTM5Ng==&mid=2247486283&idx=1&sn=4b63f438df33291a3deb1052bea31347&chksm=fe4b3e90c93cb786a54407a4f7e552b2c8b28478b28df852e41f5d9e2c991761dddbc9a5a813&scene=21#wechat_redirect)

`[6]` [PostgreSQL Monitoring System Pigsty Overview](/article/monitoring-intro/)
