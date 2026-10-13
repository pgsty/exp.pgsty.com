---
title: "Monitoring Table Size in PostgreSQL"
date: 2018-05-14
authors: [vonng]
summary: "Measure PostgreSQL table storage, including indexes, TOAST, and relation forks."
tags: [PostgreSQL, PG Admin, Monitoring]
---

This 2018 article explains physical storage for ordinary PostgreSQL tables.

### Table Storage Layout

An ordinary table has its own storage and may also have a TOAST table:

* Main table: stores row data, `relkind='r'`.
* TOAST table: stores out-of-line values when needed, `relkind='t'`. Some tables have no TOAST table.

A table and each of its indexes are separate **relations**:

* Main relation: stores tuples.
* Index relation: stores index tuples.

Each **relation** may have **four forks**:

* main: the relation's main file, numbered 0

* fsm: stores information about free space in the main fork, numbered 1
* vm: stores information about visibility in the main fork, numbered 2
* init: used for unlogged tables and indexes, numbered 3

Each fork is stored in one or more files. The default segment size is 1 GiB; it can be changed when PostgreSQL is built.

To account for a table’s storage, include these relations:

* Main table's main relation (single)
* Main table's indexes (multiple)
* TOAST table's main relation (single)
* TOAST table's index (single)

Include every fork that exists for each relation: `main`, `fsm`, `vm`, and `init`. The `init` fork applies to unlogged relations.

### Getting Table's Associated Relations

The following query lists relation OIDs. Forks share a relation OID; they do not have independent OIDs. The left join keeps tables that have no TOAST table:

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

### Statistical Functions

PostgreSQL provides [size functions](https://www.postgresql.org/docs/10/functions-admin.html#FUNCTIONS-ADMIN-DBSIZE) for each part:

| Function                        | Statistical Scope                                        |
| ------------------------------- | -------------------------------------------------------- |
| `pg_total_relation_size(oid)`  | Entire relation, including table, indexes, TOAST, etc.  |
| `pg_indexes_size(oid)`         | Space occupied by relation's index portion              |
| `pg_table_size(oid)`            | Table forks and TOAST, including the TOAST index; excludes the main table’s indexes            |
| `pg_relation_size(oid)`        | Get size of a relation's main file part (main fork)    |
| `pg_relation_size(oid, 'main')` | Get relation's `main` fork size                         |
| `pg_relation_size(oid, 'fsm')`  | Get relation's `fsm` fork size                          |
| `pg_relation_size(oid, 'vm')`   | Get relation's `vm` fork size                           |
| `pg_relation_size(oid, 'init')` | Get relation's `init` fork size                         |

For routine monitoring, group storage into table and index space. For ordinary tables, `pg_table_size` plus `pg_indexes_size` equals `pg_total_relation_size`.

The following identities describe the components; they are formulas, not a complete SQL query:

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

A TOAST table has one index. Use `pg_total_relation_size(reltoastrelid)` to include both the TOAST table and its index.

### Example: Table and Related Relation Sizes

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

Wrap the query in a table-returning function for reuse. Replace the example OID with a table in your database:

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

Each row’s `size` includes that relation’s attached storage. The main table row
already includes its indexes and TOAST, so do not sum this column. `tuples` and
`pages` come from planner statistics and can lag behind current data.

Sample result from the original environment:

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

### Example: Relation Size Details Summary

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
