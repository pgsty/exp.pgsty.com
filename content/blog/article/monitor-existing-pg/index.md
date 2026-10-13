---
title: "Monitor Existing PostgreSQL with Pigsty: RDS, PolarDB, and Self-Hosted Databases"
date: 2023-09-17
authors: [vonng]
summary: >
  Deploy Pigsty on ECS and connect existing PostgreSQL databases, using Alibaba Cloud PolarDB and RDS for PostgreSQL as examples.
tags: [Pigsty, Monitoring, RDS]
---

This tutorial describes Pigsty and Alibaba Cloud services as used in September 2023. Commands, prices, and dashboard details reflect that period.

Pigsty is a PostgreSQL distribution. You can also use it solely to monitor PostgreSQL and hosts. This tutorial uses Alibaba Cloud as an example: install Pigsty on one ECS instance, then connect existing PolarDB and RDS for PostgreSQL databases.

[Video tutorial](https://mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl&action=mpvideo&auto=0&vid=wxv_3109126349086162945)

## Procedure

The tutorial has four steps:

1. Create an ECS instance for Pigsty.
2. Install the full single-node Pigsty environment on it.
3. Configure the monitoring user, schemas, views, and access lists in PolarDB or RDS.
4. Register the database instances with Pigsty monitoring.

At the time of writing, the example required an Alibaba Cloud account with a balance above CNY 100 for pay-as-you-go resources. The example resources cost about CNY 4 per hour.

## Why add this monitoring system?

Cloud providers already offer RDS monitoring. I needed more metrics to analyze slow queries, diagnose faults, and assess capacity, so I added this system.

![Cloud database monitoring example](01.webp)

![Cloud monitoring detail](02.webp)

Pigsty uses Grafana and Prometheus, packaged as an INFRA module that can be installed together. Components managed by Pigsty are added to monitoring: hosts, HAProxy, PostgreSQL, PgBouncer, etcd, Redis, MinIO, and the monitoring infrastructure itself. The supplied dashboards and alert rules show system status and support troubleshooting.

![Overview of Pigsty dashboards](03.webp)

At the time of this article, a full deployment used more than 3,000 kinds of metrics for databases and supporting components. Dashboards organize the data by cluster, instance, and object. They show activity on tables, indexes, and functions, as well as cluster totals. Links switch between views; the time selector compares current activity with historical trends.

![Dashboard navigation and drill-down](04.webp)

For an existing PostgreSQL database, especially a managed cloud service, available data depends on the service's access interfaces. This setup usually lacks host, high-availability, connection-pool, and native database log data. It mainly uses PostgreSQL's own metrics.

Explore the [public demo](https://demo.pigsty.cc) to see the monitoring interface.

## Create an ECS instance

The setup shown here used an x86_64 ECS instance running EL 7–9, with Rocky Linux 8.6 or 9.1 recommended at the time. The minimum size was one CPU and 2 GB of memory. You could create it in the cloud console or use Pigsty's Terraform template.

The demonstration template assigned the private address `10.10.10.10`, the example password `PigstyDemo4`, and a public IP address for access.

![ECS resource configuration](05.webp)

![Terraform provisioning](06.webp)

## Install single-node Pigsty on ECS

After logging in to ECS, the installation workflow was:

```bash
bash -c "$(curl -fsSL https://get.pigsty.cc/latest)"  # Download Pigsty
cd ~/pigsty
./bootstrap                                        # Download the offline packages
./configure                                        # Configure Pigsty
vi pigsty.yml                                      # Set passwords and other local settings
./install.yml                                      # Install the single-node environment
```

With the offline packages, the full installation took about ten minutes. The current procedure is in the [Pigsty installation guide](https://pigsty.io/docs/setup/install/).

After installation, Grafana was available on port 3000 of the ECS public address. It included monitoring for the new environment itself. The example installation used the default Grafana credentials `admin` / `pigsty`.

![Grafana after installation](07.webp)

Use a domain name and HTTPS for the web interface. Replace the example passwords and restrict access to the monitoring system.

![Pigsty web access](08.webp)

## Configure PolarDB or RDS for monitoring

The exporter needs a connection URL that it can reach from ECS, a monitoring account with the required read permissions, and any extensions used by the selected collectors.

For the PolarDB example:

1. Create the cluster in a network reachable from ECS. This example used the same availability zone and subnet.
2. Create the privileged administration account `dbuser_dba` for initial configuration.
3. Add the ECS private address, `10.10.10.10`, to the cluster access allowlist.
4. Create a database, named `test` in this example.

Connect as the administrator to configure the monitoring role. Substitute your cluster endpoint and use a password prompt:

```bash
psql -h your-cluster.polardbpg.rds.aliyuncs.com -p 1921 -U dbuser_dba -d test -W
```

Create a dedicated monitoring user with this account, or create it through the cloud console.

![Monitoring account configuration](09.webp)

Install `pg_stat_statements` to collect query-level statistics, including call counts and execution time.

## Register existing databases

To add RDS and PolarDB instances, provide their identities and connection settings in `pigsty.yml`. In the version used here, `all.children.infra.vars.pg_exporters` was a dictionary: each key was a unique local exporter port, and each value described a target database instance.

![Remote exporter configuration](10.webp)

This example registered three clusters:

- `pg-polar`: a PolarDB cluster with one primary and one replica.
- `pg-rds`: a basic, single-node RDS for PostgreSQL instance.
- `pg-rdsha`: a high-availability RDS cluster with an additional read-only node.

The screenshot shows the configuration. Usually, the fields to change were `pg_cluster`, `pg_seq`, and `pg_host`, plus `pg_port` when the port was not 5432. Other settings could be overridden as needed.

After defining the targets, add each cluster to monitoring:

```bash
bin/pgmon-add pg-polar
bin/pgmon-add pg-rds
bin/pgmon-add pg-rdsha
```

The three clusters then appear in Pigsty:

![Registered database clusters](11.webp)

Click a cluster or instance name in light blue to open its PGRDS dashboard.

![PGRDS cluster dashboard](12.webp)

![PGRDS instance dashboard](13.webp)

The opening screen shows cluster members, health, the database list and navigation, and 13 core metrics. Click a panel to inspect the details.

![Core database metrics](14.webp)

Links within charts let you move between PGRDS Cluster and PGRDS Instance, from a cluster overview to one instance and back.

![Cluster and instance navigation](15.webp)

The Overview and Database dashboards remain available. They show details such as QPS and response time for each query class, or reads and writes on each table.

![Database overview](16.webp)

![Query metrics](17.webp)

![Database object metrics](18.webp)

![Table activity](19.webp)

Pigsty can also query the database catalog directly through an optional data source. This provides views of current lock waits and top SQL statements.

![Catalog exploration](20.gif)

![SQL and lock statistics](21.webp)

For more detail, see the [Pigsty documentation](https://pigsty.io), explore the [demo](https://demo.pigsty.cc), or watch the [video tutorial](https://mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl&action=mpvideo&auto=0&vid=wxv_3109126349086162945).

To join the PGSQL × Pigsty discussion group, search for `pigsty-cc` on WeChat and contact the Pigsty assistant.
