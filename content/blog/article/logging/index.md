---
title: "PostgreSQL Server Log Configuration"
date: 2018-02-06
authors: [vonng]
summary: >
  CSV logs can be imported into PostgreSQL tables or queried through file_fdw for analysis.
tags: [PostgreSQL, PG Admin, Monitoring]
---

This article was written in 2018. The table definitions below use the 23-column PostgreSQL 10 CSV format, and the Filebeat example uses the legacy `prospectors` configuration.

CSV logs can be imported into PostgreSQL tables or queried through `file_fdw` for analysis.

## Log Configuration

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

The last three settings collect runtime statistics; they do not control log output.
`logging_collector` and `track_activity_query_size` require a server restart.
The weekday filename repeats each week. Configure rotation and retention to match
how long you need to keep the files.

## Log Collection

The original setup used Filebeat to forward local files to Kafka. Replace the
paths and broker address with your own. This legacy example starts at the end of
existing files and joins lines by a timestamp pattern, with a 20-line limit. It
does not provide general CSV record framing for arbitrary multiline messages.

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

## CSV Log Format

PostgreSQL can query its logs as rows. The following table matches the
[PostgreSQL 10 CSV fields](https://www.postgresql.org/docs/10/runtime-config-logging.html#RUNTIME-CONFIG-LOGGING-CSVLOG).
Later server versions add columns; use the table definition for the server that
wrote the log:

```sql
-- Log table structure
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

## Importing Logs

Import a closed CSV log file with `COPY`. The server must be able to read the
file. For a file on the client machine, use psql’s `\copy`. Import complete files after rotation, and import each file only once.

```sql
COPY postgresql_log FROM '/pg/data/log/postgresql-Mon.csv' WITH (FORMAT csv);
```

## Mapping Logs

Use `file_fdw` to query local CSV files without copying them into a table. Run the
setup with the required extension and server-file privileges. The example assumes
English weekday names and existing files under `/pg/data/log`; adjust the paths
to match the log output. Query an individual child table if some weekday files
do not yet exist.

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

## Extracting Log Fields

These functions extract duration, statement text, and IPv4-shaped text from
English log messages. Durations are in milliseconds. They handle the message
patterns shown here, not every extended-query or localized message format:

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
