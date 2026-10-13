---
title: "监控 PostgreSQL 表大小"
date: 2018-05-14
authors: [vonng]
summary: >
  统计 PostgreSQL 表的存储空间，包括索引、TOAST 和关系的各个分支。
tags: [PostgreSQL, PG管理, 监控]
---

本文写于 2018 年，介绍 PostgreSQL 普通表的物理存储。

### 表的空间布局

普通表包含自身存储，也可能有一张 TOAST 表：

* 本体表：存储行数据，`relkind='r'`。
* TOAST 表：按需存储行外数据，`relkind='t'`。部分表没有 TOAST 表。

表本身和它的每个索引都是独立的 **关系（Relation）**：

* 主体关系：存储元组。
* 索引关系：存储索引元组。

每个 **关系** 又可能会有 **四种分支**：

* main: 关系的主文件，编号为0

* fsm：保存关于main分支中空闲空间的信息，编号为1
* vm：保存关于main分支中可见性的信息，编号为2
* init：用于不写 WAL 的 unlogged 表和索引，编号为3

每个分支存储在一个或多个文件中。默认每段最大 1 GiB，编译 PostgreSQL 时可以修改此值。

统计一张表的存储，需要计入以下关系：

* 本体表的主体关系（单个）
* 本体表的索引（多个）
* TOAST表的主体关系（单个）
* TOAST表的索引（单个）

对每个关系，应计入实际存在的 `main`、`fsm`、`vm` 和 `init` 分支。`init` 用于 unlogged 关系。

### 获取表的附属关系

以下查询列出关系 OID。分支共享所属关系的 OID，没有独立 OID。左连接会保留没有 TOAST 表的普通表：

```sql
select
  nsp.nspname,
  rel.relname,
  rel.relnamespace    as nspid,
  rel.oid             as relid,
  rel.reltoastrelid   as toastid,
  toastind.indexrelid as toastindexid,
  ind.indexes
from
  pg_namespace nsp
  join pg_class rel on nsp.oid = rel.relnamespace
  CROSS JOIN LATERAL (select array_agg(indexrelid) as indexes from pg_index where indrelid = rel.oid) ind
  LEFT JOIN LATERAL (select indexrelid from pg_index where indrelid = rel.reltoastrelid) toastind ON true
where nspname not in ('pg_catalog', 'information_schema') and rel.relkind = 'r';
```

```text
 nspname |  relname   |  nspid  |  relid  | toastid | toastindexid |      indexes
---------+------------+---------+---------+---------+--------------+--------------------
 public  | aoi        | 4310872 | 4320271 | 4320274 |      4320276 | {4325606,4325605}
 public  | poi        | 4310872 | 4332324 | 4332327 |      4332329 | {4368886}
```

### 统计函数

PostgreSQL 提供了对应的[大小统计函数](https://www.postgresql.org/docs/10/functions-admin.html#FUNCTIONS-ADMIN-DBSIZE)：

| 函数                            | 统计口径                                 |
| ------------------------------- | ---------------------------------------- |
| `pg_total_relation_size(oid)`  | 整个关系，包括表，索引，TOAST等。        |
| `pg_indexes_size(oid)`         | 关系索引部分所占空间                     |
| `pg_table_size(oid)`            | 表的各个分支和 TOAST（含 TOAST 索引），不含主表索引               |
| `pg_relation_size(oid)`        | 获取一个关系主文件部分的大小（main分支） |
| `pg_relation_size(oid, 'main')` | 获取关系 `main` 分支大小                   |
| `pg_relation_size(oid, 'fsm')`  | 获取关系 `fsm` 分支大小                    |
| `pg_relation_size(oid, 'vm')`   | 获取关系 `vm` 分支大小                     |
| `pg_relation_size(oid, 'init')` | 获取关系 `init` 分支大小                   |

日常监控可将存储分为表与索引两部分。对普通表，`pg_table_size` 与 `pg_indexes_size` 之和等于 `pg_total_relation_size`。

各部分满足以下关系。这是计算公式，不是完整的 SQL 查询：

```text
 pg_table_size(relid)
     = pg_relation_size(relid, 'main')
     + pg_relation_size(relid, 'fsm')
     + pg_relation_size(relid, 'vm')
     + pg_relation_size(relid, 'init')
     + COALESCE(pg_total_relation_size(reltoastrelid), 0)

 pg_indexes_size(relid)
     = (SELECT COALESCE(sum(pg_total_relation_size(indexrelid)), 0)
        FROM pg_index WHERE indrelid = relid)
```

TOAST 表有一个索引。使用 `pg_total_relation_size(reltoastrelid)` 可计算 TOAST 表及其索引的总大小。

### 例：统计表及其附属关系大小

```sql
SELECT
  oid,
  relname,
  relnamespace::RegNamespace::Text               as nspname,
  relkind                                        as relkind,
  reltuples                                      as tuples,
  relpages                                       as pages,
  pg_total_relation_size(oid)                    as size
  FROM pg_class
WHERE oid = ANY(array(SELECT 16418 as id -- main
UNION ALL SELECT indexrelid FROM pg_index WHERE indrelid = 16418 -- index
UNION ALL SELECT reltoastrelid FROM pg_class WHERE oid = 16418)); -- toast
```

可将查询包装为返回表的函数，方便复用。请将示例 OID 替换为实际数据库中的表：

```sql
CREATE OR REPLACE FUNCTION pg_table_size_detail(relation RegClass)
  RETURNS TABLE(
    id      oid,
    pid     oid,
    relname name,
    nspname text,
    relkind "char",
    tuples  bigint,
    pages   integer,
    size    bigint
  )
AS $$
BEGIN
  RETURN QUERY
  SELECT
    rel.oid,
    relation::oid,
    rel.relname,
    rel.relnamespace :: RegNamespace :: Text as nspname,
    rel.relkind                              as relkind,
    rel.reltuples::bigint                    as tuples,
    rel.relpages                             as pages,
    pg_total_relation_size(rel.oid)          AS size
  FROM pg_class rel
  WHERE rel.oid = ANY (array(
      SELECT relation::oid AS id -- main
      UNION ALL SELECT indexrelid FROM pg_index WHERE indrelid = relation -- index
      UNION ALL SELECT reltoastrelid FROM pg_class WHERE oid = relation)); -- toast
END;
$$
LANGUAGE PlPgSQL;

SELECT * FROM pg_table_size_detail(16418);

```

每行 `size` 都包含该关系的附属存储。主表行已经包含索引和 TOAST，不能再将这一列求和。`tuples` 和 `pages` 来自规划器统计，可能落后于实际数据。

原环境中的返回结果：

```text
geo=# select * from  pg_table_size_detail(4325625);
   id    |   pid   |        relname        | nspname  | relkind |  tuples  |  pages  |    size
---------+---------+-----------------------+----------+---------+----------+---------+-------------
 4325628 | 4325625 | pg_toast_4325625      | pg_toast | t       |   154336 |   23012 |   192077824
 4419940 | 4325625 | idx_poi_adcode_btree  | gaode    | i       | 62685464 |  172058 |  1409499136
 4419941 | 4325625 | idx_poi_cate_id_btree | gaode    | i       | 62685464 |  172318 |  1411629056
 4419942 | 4325625 | idx_poi_lat_btree     | gaode    | i       | 62685464 |  172058 |  1409499136
 4419943 | 4325625 | idx_poi_lon_btree     | gaode    | i       | 62685464 |  172058 |  1409499136
 4419944 | 4325625 | idx_poi_name_btree    | gaode    | i       | 62685464 |  335624 |  2749431808
 4325625 | 4325625 | gaode_poi             | gaode    | r       | 62685464 | 2441923 | 33714962432
 4420005 | 4325625 | idx_poi_position_gist | gaode    | i       | 62685464 |  453374 |  3714039808
 4420044 | 4325625 | poi_position_geohash6 | gaode    | i       | 62685464 |  172058 |  1409499136
```

### 例：关系大小详情汇总

```sql
select
  nsp.nspname,
  rel.relname,
  rel.relnamespace    as nspid,
  rel.oid             as relid,
  rel.reltoastrelid   as toastid,
  toastind.indexrelid as toastindexid,
  pg_total_relation_size(rel.oid)  as size,
  pg_relation_size(rel.oid) + pg_relation_size(rel.oid,'fsm')
  + pg_relation_size(rel.oid,'vm')
  + pg_relation_size(rel.oid,'init') AS relsize,
  pg_indexes_size(rel.oid)         as indexsize,
  COALESCE(pg_total_relation_size(reltoastrelid), 0) AS toastsize,
  ind.indexids,
  ind.indexnames,
  ind.indexsizes
from pg_namespace nsp
  join pg_class rel on nsp.oid = rel.relnamespace
  LEFT JOIN LATERAL (select indexrelid from pg_index where indrelid = rel.reltoastrelid) toastind ON true
  CROSS JOIN LATERAL (select array_agg(indexrelid ORDER BY indexrelid) AS indexids,
                      array_agg(indexrelid::regclass ORDER BY indexrelid) AS indexnames,
                      array_agg(pg_total_relation_size(indexrelid) ORDER BY indexrelid) AS indexsizes
              from pg_index where indrelid = rel.oid) ind
where nspname not in ('pg_catalog', 'information_schema') and rel.relkind = 'r';
```
