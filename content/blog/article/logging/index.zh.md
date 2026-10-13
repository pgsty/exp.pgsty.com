---
title: "PostgreSQL 服务器日志配置"
date: 2018-02-06
authors: [vonng]
summary: >
  CSV 日志可以导入 PostgreSQL 表，也可以通过 file_fdw 直接查询。
tags: [PostgreSQL, PG管理, 监控]
---

本文写于 2018 年。下方表结构对应 PostgreSQL 10 的 23 列 CSV 格式，Filebeat 示例使用当时的 `prospectors` 配置。

CSV 日志可以导入 PostgreSQL 表，也可以通过 `file_fdw` 直接查询。

## 日志配置

```ini
log_destination = 'csvlog'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%a.log'
log_min_duration_statement = 1000
log_checkpoints = on
log_lock_waits = on
log_statement = 'ddl'
log_replication_commands = on
log_timezone = 'UTC'
log_autovacuum_min_duration = 1000

track_io_timing = on
track_functions = all
track_activity_query_size = 16384
```

最后三项用于运行统计，不控制日志输出。`logging_collector` 和 `track_activity_query_size` 需要重启服务器生效。按星期命名的文件每周会重用同一名称，应按所需保留时间设置轮转和清理规则。

## 日志收集

原方案使用 Filebeat 将本地日志转发到 Kafka。请替换文件路径和 Kafka 地址。这个旧版示例从已有文件末尾开始读取，按时间戳模式合并行，最多合并 20 行；它不能完整识别任意多行消息的 CSV 记录边界。

```yaml
filebeat.prospectors:
  - type: log
    enabled: true
    paths:
      - /pg/data/log/postgresql-*.csv
    document_type: db-trace
    tail_files: true
    multiline.pattern: '^20\d\d-\d\d-\d\d'
    multiline.negate: true
    multiline.match: after
    multiline.max_lines: 20

max_cpus: 1

filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: false

queue.mem:
  events: 1024
  flush.min_events: 0
  flush.timeout: 1s

output.kafka:
  hosts: ["kafka.example.com:9092"]
  topics:
    - topic: 'log.db'
```

## CSV 日志格式

将日志映射为表后，就能用 SQL 分析。下列表结构与 [PostgreSQL 10 的 CSV 字段](https://www.postgresql.org/docs/10/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG) 一致。后续版本增加了列，导入时应使用产生日志的服务器版本对应的表结构：

```sql
-- 日志表结构
create table postgresql_log
(
  log_time               timestamp(3) with time zone,
  user_name              text,
  database_name          text,
  process_id             integer,
  connection_from        text,
  session_id             text   not null,
  session_line_num       bigint not null,
  command_tag            text,
  session_start_time     timestamp with time zone,
  virtual_transaction_id text,
  transaction_id         bigint,
  error_severity         text,
  sql_state_code         text,
  message                text,
  detail                 text,
  hint                   text,
  internal_query         text,
  internal_query_pos     integer,
  context                text,
  query                  text,
  query_pos              integer,
  location               text,
  application_name       text,
  PRIMARY KEY (session_id, session_line_num)
);
```

## 导入日志

用 `COPY` 导入已经关闭的 CSV 日志文件，服务器需要有文件读取权限。文件在客户端机器上时，改用 psql 的 `\copy`。日志轮转后再导入完整文件，每个文件只导入一次。

```sql
COPY postgresql_log FROM '/pg/data/log/postgresql-Mon.csv' WITH (FORMAT csv);
```

## 映射日志

`file_fdw` 可以直接查询本地 CSV 文件，无需先复制到表中。用具备扩展和服务器文件访问权限的角色执行以下设置。示例假定文件位于 `/pg/data/log`，且星期名为英文缩写，请按实际输出调整路径。部分星期文件尚不存在时，先查询已有文件对应的子表。

```sql
CREATE SCHEMA IF NOT EXISTS monitor;

-- This session only
SET search_path = monitor, pg_catalog;

-- extension
CREATE EXTENSION IF NOT EXISTS file_fdw WITH SCHEMA monitor;

-- log parent table: empty
CREATE TABLE monitor.pg_log
(
  log_time               timestamp(3) with time zone,
  user_name              text,
  database_name          text,
  process_id             integer,
  connection_from        text,
  session_id             text,
  session_line_num       bigint,
  command_tag            text,
  session_start_time     timestamp with time zone,
  virtual_transaction_id text,
  transaction_id         bigint,
  error_severity         text,
  sql_state_code         text,
  message                text,
  detail                 text,
  hint                   text,
  internal_query         text,
  internal_query_pos     integer,
  context                text,
  query                  text,
  query_pos              integer,
  location               text,
  application_name       text,
  PRIMARY KEY (session_id, session_line_num)
);
COMMENT ON TABLE monitor.pg_log IS 'PostgreSQL csv log schema';
-- local file server
CREATE SERVER IF NOT EXISTS pg_log FOREIGN DATA WRAPPER file_fdw;
-- Change filename to actual path
CREATE FOREIGN TABLE IF NOT EXISTS monitor.pg_log_mon() INHERITS (monitor.pg_log) SERVER pg_log OPTIONS (filename '/pg/data/log/postgresql-Mon.csv', format 'csv');
CREATE FOREIGN TABLE IF NOT EXISTS monitor.pg_log_tue() INHERITS (monitor.pg_log) SERVER pg_log OPTIONS (filename '/pg/data/log/postgresql-Tue.csv', format 'csv');
CREATE FOREIGN TABLE IF NOT EXISTS monitor.pg_log_wed() INHERITS (monitor.pg_log) SERVER pg_log OPTIONS (filename '/pg/data/log/postgresql-Wed.csv', format 'csv');
CREATE FOREIGN TABLE IF NOT EXISTS monitor.pg_log_thu() INHERITS (monitor.pg_log) SERVER pg_log OPTIONS (filename '/pg/data/log/postgresql-Thu.csv', format 'csv');
CREATE FOREIGN TABLE IF NOT EXISTS monitor.pg_log_fri() INHERITS (monitor.pg_log) SERVER pg_log OPTIONS (filename '/pg/data/log/postgresql-Fri.csv', format 'csv');
CREATE FOREIGN TABLE IF NOT EXISTS monitor.pg_log_sat() INHERITS (monitor.pg_log) SERVER pg_log OPTIONS (filename '/pg/data/log/postgresql-Sat.csv', format 'csv');
CREATE FOREIGN TABLE IF NOT EXISTS monitor.pg_log_sun() INHERITS (monitor.pg_log) SERVER pg_log OPTIONS (filename '/pg/data/log/postgresql-Sun.csv', format 'csv');

```

## 提取日志字段

这些函数从英文日志消息中提取耗时、语句文本和形似 IPv4 的文本。耗时单位为毫秒。函数仅处理示例中的消息格式，不覆盖所有扩展查询协议或本地化消息：

```sql
CREATE OR REPLACE FUNCTION extract_duration(statement TEXT)
  RETURNS FLOAT AS $$
DECLARE
  found_duration BOOLEAN;
BEGIN
  SELECT position('duration' in statement) > 0
  into found_duration;
  IF found_duration
  THEN
    RETURN (SELECT regexp_matches [1] :: FLOAT
            FROM regexp_matches(statement, '^duration: ([0-9]+(?:\.[0-9]+)?) ms')
            LIMIT 1);
  ELSE
    RETURN NULL;
  END IF;
END
$$
LANGUAGE plpgsql
IMMUTABLE;

CREATE OR REPLACE FUNCTION extract_statement(statement TEXT)
  RETURNS TEXT AS $$
DECLARE
  found_statement BOOLEAN;
BEGIN
  SELECT position('statement' in statement) > 0
  into found_statement;
  IF found_statement
  THEN
    RETURN (SELECT regexp_matches [1]
            FROM regexp_matches(statement, 'statement: (.*)')
            LIMIT 1);
  ELSE
    RETURN NULL;
  END IF;
END
$$
LANGUAGE plpgsql
IMMUTABLE;

CREATE OR REPLACE FUNCTION extract_ip(app_name TEXT)
  RETURNS TEXT AS $$
DECLARE
  ip TEXT;
BEGIN
  SELECT regexp_matches [1]
  into ip
  FROM regexp_matches(app_name, '(\d+\.\d+\.\d+\.\d+)')
  LIMIT 1;
  RETURN ip;
END
$$
LANGUAGE plpgsql
IMMUTABLE;
```
