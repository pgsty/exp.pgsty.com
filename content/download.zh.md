---
title: "下载 PG Exporter"
linkTitle: "下载"
description: "选择、安装、配置、启用并验证 PG Exporter 软件包、压缩包、容器、Pigsty 自动化或源码构建"
weight: 25
icon: fa-solid fa-download
categories: [指南]
search_keywords: [下载, 安装, 软件包, RPM, DEB, YUM, APT, 容器, Docker, 二进制, 校验和, 压缩包, Pigsty, 源码]
search_boost: 1.5
layout: landing
landing: download
---

<!-- 落地页布局渲染的是 data/landing/download/<lang>.yaml，而不是这段正文。
     下面这段是本页的可检索文本：OINK 的离线索引会跳过没有原始正文的页面，
     而这一页是读者按产物名称查找的顶层导航入口。 -->

从 Pigsty 的 APT/YUM 仓库、固定版本的 RPM 或 DEB 软件包、面向 Linux、macOS 与
Windows 的发布压缩包、多架构容器镜像 `pgsty/pg_exporter`、Pigsty 自动化，或指定标签的
源码构建来安装 PG Exporter。每条路径运行的都是同一个二进制与同一套声明式采集器，
每个发布产物都带 SHA-256 摘要。安装之后创建监控角色、提供连接串、执行
`pg_exporter --dry-run`，确认 `:9630/metrics` 上的 `pg_up 1`，再把目标加入 Prometheus。
