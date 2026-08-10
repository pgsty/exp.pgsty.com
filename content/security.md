---
title: "Security"
linkTitle: "Security"
description: "Least-privilege database access, secret handling, TLS, HTTP authentication, and network exposure"
weight: 60
icon: fa-solid fa-shield-halved
categories: [Guide]
---

`pg_exporter` sits between two trust domains: it authenticates to PostgreSQL or PgBouncer, then exposes metrics and management endpoints over HTTP. Secure both sides independently. Database TLS does not protect the HTTP listener, and HTTP Basic Auth does not reduce database privileges.

## Threat Surface

| Surface | Sensitive capability | Primary control |
|:---|:---|:---|
| PostgreSQL connection | Read monitoring views and execute collector SQL | Dedicated login, `pg_monitor`, `pg_hba.conf`, TLS |
| Target URL | Contains host, user, and often a password | `.pgpass`, secret file, file permissions, secret manager |
| `/metrics` | Reveals topology, object names, workload, and capacity | Private network, firewall, TLS/auth |
| `/explain` and `/stat` | Reveal collector definitions, eligibility, timing, and errors | Restrict or authenticate HTTP access |
| `/reload` | Triggers config parsing and an atomic query-plan replacement | Restrict or authenticate HTTP access |
| Collector SQL | Consumes database resources and may expose labels | Query review, least privilege, timeout, TTL, cardinality review |
{.full-width}

## Use a Dedicated Database Role

For PostgreSQL 10+, the built-in `pg_monitor` role covers the read permissions needed by the default collectors:

```sql
CREATE ROLE monitor
  WITH LOGIN
       PASSWORD 'replace-this-secret'
       CONNECTION LIMIT 5;

GRANT pg_monitor TO monitor;
```

Do not run the exporter as a superuser merely to avoid reviewing permissions. Optional custom collectors may need explicit grants on their own views, functions, or schemas; grant those objects individually.

For PgBouncer, connect to the admin database with an account permitted by `stats_users` or `admin_users`, depending on local policy. The exporter uses the admin `SHOW` interface rather than PostgreSQL catalog queries in that mode.

## Keep Passwords Out of Process Arguments

The target URL is resolved in this order:

1. `--url` / `-u`
2. `PG_EXPORTER_URL`
3. `PGURL`
4. the file named by `PG_EXPORTER_URL_FILE`
5. `postgresql:///?sslmode=disable`

Command arguments may be visible in process listings. Prefer one of these patterns:

### `.pgpass`

```text
db.example.com:5432:*:monitor:replace-this-secret
```

```bash
chmod 600 ~/.pgpass
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full'
```

RPM/DEB services run as `prometheus`. Since v1.4.0 that account's HOME is `/var/lib/prometheus`, but the package does not create the directory:

```bash
sudo install -d -o prometheus -g prometheus -m 0750 /var/lib/prometheus
sudo install -o prometheus -g prometheus -m 0600 ./pgpass /var/lib/prometheus/.pgpass
```

### Secret file

`PG_EXPORTER_URL_FILE` is convenient for systemd credentials, Docker/Kubernetes Secret mounts, and other file-based secret delivery:

```bash
export PG_EXPORTER_URL_FILE=/run/secrets/pg_exporter_url
pg_exporter --config=/etc/pg_exporter.yml
```

The file should contain one URL plus optional surrounding whitespace. A missing or unreadable explicitly configured file is fatal. Logs redact passwords found in URL user-info and `password=` query parameters, but log redaction is not a substitute for protecting the source secret.

## Secure the Database Connection

When `sslmode` is omitted, pg_exporter intentionally adds `sslmode=disable` for common same-host deployments. That default is unsafe for an untrusted network. Remote targets should select an explicit libpq TLS policy:

```bash
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pg_exporter/ca.crt'
```

Use `verify-full` when possible so the certificate chain and hostname are both verified. `require` encrypts traffic but does not provide the same server-identity assurance.

The official Docker image is based on `scratch` and has no system CA bundle. Mount the required CA file into the container and reference that exact path in `sslrootcert`.

## Minimize HTTP Exposure

If Prometheus runs on the same host, bind only to loopback:

```bash
pg_exporter --web.listen-address=127.0.0.1:9630
```

For remote scraping, allow only monitoring networks at the firewall or service-mesh layer. Remember that the listener includes management endpoints; there is no separate management port.

### TLS and Basic Auth

`--web.config.file` uses the Prometheus exporter-toolkit format and is re-read on every HTTP request. A minimal example:

```yaml
tls_server_config:
  cert_file: /etc/pg_exporter/web.crt
  key_file: /etc/pg_exporter/web.key
  min_version: TLS12

basic_auth_users:
  prometheus: "$2y$10$replace_with_a_bcrypt_hash"
```

```bash
pg_exporter --web.config.file=/etc/pg_exporter/web.yml
```

Generate a bcrypt hash without placing the cleartext password in the file, for example with `htpasswd -nBC 10 prometheus`. See the authoritative [exporter-toolkit web configuration](https://github.com/prometheus/exporter-toolkit/blob/master/docs/web-configuration.md) for mTLS, headers, and rate limiting.

With Basic Auth enabled, configure the Prometheus scrape job accordingly:

```yaml
scrape_configs:
  - job_name: postgresql
    scheme: https
    basic_auth:
      username: prometheus
      password_file: /etc/prometheus/secrets/pg_exporter_password
    tls_config:
      ca_file: /etc/prometheus/ca/pg_exporter-ca.crt
    static_configs:
      - targets: ['db.example.com:9630']
```

## Protect Configuration Files

The release packages install `/etc/pg_exporter.yml` and `/etc/default/pg_exporter` for the `prometheus` user with restrictive modes. Preserve those ownership and mode choices when copying or templating files. Do not place database passwords in the collector YAML; it is for queries and metric metadata, not connection secrets.

Review custom labels before deployment. Database names, customer identifiers, tenant names, and SQL fingerprints can become Prometheus labels and spread to remote storage, alerts, and dashboards.

## Production Checklist

- Dedicated non-superuser database account with a small connection limit
- Explicit `pg_hba.conf` rule and network source restriction
- `.pgpass` or secret-file delivery instead of a password in command arguments
- `sslmode=verify-full` plus a trusted CA for remote database connections
- Loopback/private binding or firewall restrictions for port 9630
- HTTP TLS/auth when the port crosses a trust boundary
- Management endpoints treated as sensitive
- Custom SQL reviewed for privileges, timeout, TTL, and label cardinality
- Secret and certificate rotation tested without exposing values in logs or process listings

See [Production Deployment](/deploy/) for service examples and [Troubleshooting](/troubleshooting/) for TLS, credential, and endpoint failure modes.
