---
title: "Security"
linkTitle: "Security"
description: "Least-privilege database access, secret handling, TLS, HTTP authentication, and network exposure"
weight: 60
icon: fa-solid fa-shield-halved
categories: [Guide]
---

Configure database access and HTTP access separately. Use a dedicated monitoring role for SQL, protect its credentials, and restrict the HTTP listener to monitoring clients.

## Access to Protect

| Access | What it permits or reveals | Control |
|:---|:---|:---|
| PostgreSQL connection | Read monitoring views and execute collector SQL | Dedicated login, `pg_monitor`, `pg_hba.conf`, TLS |
| Target URL | Contains host, user, and often a password | `.pgpass`, secret file, file permissions, secret manager |
| `/metrics` | Reveals topology, object names, workload, and capacity | Private network, firewall, TLS/auth |
| `/explain` and `/stat` | Reveal collector definitions, selected branches, timing, and errors | Restrict or authenticate HTTP access |
| `/reload` | Reloads collector configuration | Restrict or authenticate HTTP access |
| Collector SQL | Consumes database resources and may expose labels | Query review, least privilege, timeout, TTL, cardinality review |
{.full-width .wide .expand}

## Use a Dedicated Database Role

For PostgreSQL 10+, start with a login that inherits the built-in `pg_monitor` role:

```sql
CREATE ROLE monitor
  WITH LOGIN
       PASSWORD 'replace-this-secret'
       CONNECTION LIMIT 5;

GRANT pg_monitor TO monitor;
```

On PostgreSQL 10–13, the default v1.6.0 subscription collector also needs this column grant in the exporter’s **main connection database**, not merely in the databases owning subscriptions:

```sql
GRANT SELECT (oid) ON pg_catalog.pg_subscription TO monitor;
```

It does not expose `subconninfo`. PostgreSQL 14+ needs no extra grant under the standard catalog ACLs. See [subscription identity and receiver states](/collectors/#subscription-identity-and-receiver-states) for the upgrade contract.

Grant `CONNECT` on each monitored database if your cluster has revoked it from `PUBLIC`. Grant access to optional views, functions, and schemas as needed; the exporter does not require a superuser.

Size the connection limit for the selected databases. The main target pool allows up to three connections, and each additional discovered database allows one. A limit of five suits a small target; increase it when monitoring more databases or sharing the role between exporters.

For PgBouncer, add the monitoring account to `stats_users` and connect to the `pgbouncer` admin database. The bundled collectors use `SHOW` commands and do not need `admin_users` privileges.

## Keep Passwords Out of Process Arguments

Command arguments may be visible in process listings. Prefer one of these patterns:

### `.pgpass`

First save the password in `./pgpass`:

```bash
umask 077
printf '%s\n' 'db.example.com:5432:*:monitor:replace-this-secret' > ./pgpass
```

For a foreground process, install the file in your home directory:

```bash
install -m 0600 ./pgpass ~/.pgpass
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full'
```

RPM/DEB services run as `prometheus`. The package creates new accounts with HOME `/var/lib/prometheus`; it leaves existing accounts unchanged and does not create the home directory. Check `getent passwd prometheus`, then install the password file in that account's home. For the package default:

```bash
sudo install -d -o prometheus -g prometheus -m 0750 /var/lib/prometheus
sudo install -o prometheus -g prometheus -m 0600 ./pgpass /var/lib/prometheus/.pgpass
```

### Secret file

`PG_EXPORTER_URL_FILE` is convenient for systemd credentials, Docker/Kubernetes Secret mounts, and other file-based secret delivery:

```bash
unset PG_EXPORTER_URL PGURL
export PG_EXPORTER_URL_FILE=/run/secrets/pg_exporter_url
pg_exporter --config=/etc/pg_exporter.yml
```

The file must contain one connection URL and be readable by the runtime user. Surrounding whitespace is removed. When this source is selected, an unreadable file stops startup. Clear higher-priority URL settings first; for the packaged service, remove `PG_EXPORTER_URL` from `/etc/default/pg_exporter`.

Logs mask passwords in valid URLs and `password=` parameters. Malformed-URL diagnostics omit the original connection string. Keep the source file restricted to the service account and its administrator.

Malformed URLs and invalid query escaping stop startup. Decoded query parameter names must be nonempty and contain neither Unicode whitespace nor `=`. Diagnostics use fixed text without the connection string or offending name. Rejecting these inputs prevents explicit TLS settings from being silently dropped during URL normalization. When `PG_EXPORTER_URL_FILE` is selected, empty or whitespace-only contents are also rejected; this check concerns the connection URL file, not TLS private-key files.

## Secure the Database Connection

If the URL omits `sslmode`, pg_exporter adds `sslmode=disable`. For a database connection across a network, set the TLS mode and CA path explicitly:

```bash
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full&sslrootcert=/etc/pg_exporter/ca.crt'
```

`verify-full` checks both the certificate chain and the hostname. Use a hostname listed in the server certificate. `require` encrypts the connection but does not check the hostname.

The `scratch` image includes the system CA bundle and license, but no shell. Publicly trusted certificates can use the bundled roots; mount your private CA and set `sslrootcert` when using a private PKI with `sslmode=verify-ca` or `verify-full`.

## Minimize HTTP Exposure

If Prometheus runs on the same host, bind only to loopback:

```bash
pg_exporter --web.listen-address=127.0.0.1:9630
```

For remote scraping, allow only monitoring networks at the firewall or service-mesh layer. The same listener serves metrics and management endpoints.

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

Generate a bcrypt hash without placing the cleartext password in the file, for example with `htpasswd -nBC 10 prometheus`. See the authoritative [exporter-toolkit web configuration](https://github.com/prometheus/exporter-toolkit/blob/v0.20.0/docs/web-configuration.md) for mTLS, headers, and rate limiting.

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

## Verify Access

After starting the exporter, test the authenticated endpoint from the Prometheus host:

```bash
curl --cacert /etc/prometheus/ca/pg_exporter-ca.crt \
  --user prometheus https://db.example.com:9630/metrics
```

`curl` prompts for the HTTP password. Confirm that the certificate is accepted, the response contains `pg_up 1`, and the Prometheus target is up. A request without credentials should return `401` when Basic Auth is enabled.

See [Production Deployment](/deploy/) for service examples and [Troubleshooting](/troubleshooting/) for connection and collector errors.

## Toolchain security updates

v1.6.0 uses Go 1.27.3 and refreshed modules, including `x/net` 0.62.0. It retains the security fixes documented for v1.5.0. The [release security notes](/release/v1.5.0/#security-updates) list the fixed CVEs and distinguish static symbol/package matches from unimported module advisories. Upgrade the rebuilt binary as well as its collector configuration; updating the host compiler alone does not repair an existing binary.
