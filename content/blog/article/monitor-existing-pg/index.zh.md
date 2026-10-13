---
title: "使用 Pigsty 监控现有 PostgreSQL：RDS、PolarDB 与自建数据库"
date: 2023-09-17
authors: [vonng]
summary: >
  在 ECS 上部署 Pigsty，并接入已有 PostgreSQL 数据库，以阿里云 PolarDB 与 RDS for PostgreSQL 为例。
tags: [Pigsty, 监控, RDS]
---

本文记录 2023 年 9 月的 Pigsty 与阿里云使用流程，命令、价格和界面均对应当时版本。

Pigsty 是一个 PostgreSQL 发行版，也可以单独用于监控 PostgreSQL 与主机。本文以阿里云为例，在一台 ECS 上安装 Pigsty，再接入已有的 PolarDB 与 RDS for PostgreSQL。

[视频教程](https://mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl&action=mpvideo&auto=0&vid=wxv_3109126349086162945)

## 操作流程

教程分为四步：

1. 创建用于部署 Pigsty 的 ECS 服务器。
2. 在 ECS 上完整安装单机版 Pigsty。
3. 配置 PolarDB / RDS 的监控用户、模式、视图与访问名单。
4. 将数据库实例接入 Pigsty 监控。

当时使用按量付费资源需要阿里云账户余额超过 ¥100，本例资源费用约为 ¥4 / 小时。

## 为什么增加这套监控？

云服务已经提供 RDS 监控。我在使用时，还需要更多指标来分析慢查询、诊断故障和评估容量，因此增加了这套监控。

![云数据库监控示例](01.webp)

![云监控详情](02.webp)

Pigsty 使用 Grafana 与 Prometheus，并将它们打包为可统一安装的 INFRA 模块。Pigsty 管理的主机、HAProxy、PostgreSQL、PgBouncer、etcd、Redis、MinIO，以及监控基础设施本身，都会纳入监控。预置面板和告警规则用于查看运行状态与排查问题。

![Pigsty 监控面板概览](03.webp)

当时的完整系统使用三千多类指标，覆盖数据库与配套组件。面板按集群、实例和对象组织数据，可以查看表、索引、函数的活动，也可以汇总到集群层面。页面链接用于切换视图，时间范围选择器用于比较当前状态与历史趋势。

![监控层次与页面导航](04.webp)

监控现有 PostgreSQL，特别是托管云数据库时，可获得的数据取决于服务提供的访问接口。这种接入方式通常没有主机、高可用组件、连接池和原生数据库日志数据，主要使用 PostgreSQL 自身的指标。

可以通过[公开演示](https://demo.pigsty.cc)查看监控界面。

## 创建 ECS 服务器

本例使用 x86_64 ECS，操作系统范围为 EL 7–9，当时推荐 Rocky Linux 8.6 或 9.1，最低配置为 1 核 CPU、2 GB 内存。可以在云控制台创建，也可以使用 Pigsty 提供的 Terraform 模板。

演示模板使用内网地址 `10.10.10.10` 和示例密码 `PigstyDemo4`，并分配一个公网 IP。

![ECS 资源配置](05.webp)

![Terraform 资源置备](06.webp)

## 在 ECS 上安装单机版 Pigsty

登录 ECS 后，当时的安装流程如下：

```bash
bash -c "$(curl -fsSL https://get.pigsty.cc/latest)"  # 下载 Pigsty
cd ~/pigsty
./bootstrap                                        # 下载离线软件包
./configure                                        # 配置 Pigsty
vi pigsty.yml                                      # 设置密码等本地配置
./install.yml                                      # 安装单机环境
```

使用离线包时，本例完整安装耗时约十分钟。当前流程见 [Pigsty 安装指南](https://pigsty.cc/docs/setup/install/)。

安装后，通过 ECS 公网地址的 3000 端口访问 Grafana。面板中已经包含新环境自身的监控数据。本例使用默认账号 `admin` / `pigsty`。

![安装后的 Grafana](07.webp)

使用域名和 HTTPS 访问 Web 界面。更换示例密码，并限制监控系统的访问来源。

![Pigsty Web 访问](08.webp)

## 配置 PolarDB / RDS 监控

Exporter 需要一个从 ECS 可访问的数据库连接地址、具有所需读取权限的监控账号，以及所选采集器使用的扩展。

本例的 PolarDB 配置步骤是：

1. 创建 ECS 可以访问的集群。本例使用同一可用区和子网。
2. 创建管理账号 `dbuser_dba`，用于初始配置。
3. 将 ECS 内网地址 `10.10.10.10` 加入集群访问名单。
4. 创建数据库，本例名为 `test`。

用管理账号连接数据库，将示例主机名替换为实际集群地址，并按提示输入密码：

```bash
psql -h your-cluster.polardbpg.rds.aliyuncs.com -p 1921 -U dbuser_dba -d test -W
```

用此账号创建专用监控用户，也可以通过云控制台创建。

![监控账号配置](09.webp)

安装 `pg_stat_statements`，获取查询调用次数与执行耗时等语句级统计。

## 将现有数据库接入监控

在 `pigsty.yml` 中填写数据库实例的身份与连接信息。当时的配置位置是 `all.children.infra.vars.pg_exporters`：字典的键为唯一分配的本地 Exporter 端口，值为目标实例的配置。

![远程 Exporter 配置](10.webp)

本例接入三个集群：

- `pg-polar`：一主一从的 PolarDB 集群。
- `pg-rds`：基础版单节点 RDS for PostgreSQL 实例。
- `pg-rdsha`：带有一个只读节点的高可用 RDS 集群。

上图展示了配置。通常需要修改 `pg_cluster`、`pg_seq` 与 `pg_host`；端口不是 5432 时，还需要设置 `pg_port`。其他参数按需覆盖。

定义目标后，将各集群加入监控：

```bash
bin/pgmon-add pg-polar
bin/pgmon-add pg-rds
bin/pgmon-add pg-rdsha
```

随后可以在 Pigsty 中看到这三个集群。

![接入后的数据库集群](11.webp)

点击浅蓝色的集群名或实例名，打开对应的 PGRDS 面板。

![PGRDS 集群面板](12.webp)

![PGRDS 实例面板](13.webp)

首屏显示集群成员、存活状态、数据库列表与导航，以及 13 个核心指标。点击面板可以查看详情。

![核心数据库指标](14.webp)

通过图表中的链接，可以在 PGRDS Cluster 与 PGRDS Instance 之间切换，查看集群汇总或单个实例。

![集群与实例导航](15.webp)

Overview 与 Database 面板也可用于这些实例，展示各类查询的 QPS、响应时间，以及每张表的读写活动。

![数据库概览](16.webp)

![查询指标](17.webp)

![数据库对象指标](18.webp)

![表活动](19.webp)

配置可选的数据库数据源后，还可以直接查询系统目录，查看当前锁等待与 Top SQL。

![系统目录查询](20.gif)

![SQL 与锁统计](21.webp)

更多细节见 [Pigsty 文档](https://pigsty.cc)、[公开演示](https://demo.pigsty.cc)与本文开头的视频教程。

加入 PGSQL × Pigsty 交流群，可在微信搜索 `pigsty-cc` 联系 Pigsty 小助手。
