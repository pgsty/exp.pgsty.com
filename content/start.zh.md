---
title: "快速上手"
linkTitle: "快速上手"
description: "安装 PG Exporter，连接 PostgreSQL 并验证首次抓取"
weight: 20
icon: fa-solid fa-rocket
categories: [参考]
search_keywords: [快速上手, 安装, 监控用户, pg_monitor, pg_up, 抓取, Prometheus, explain, stat]
search_boost: 1.5
layout: landing
landing: start
---

安装 PG Exporter 并创建监控角色。设置 `PG_EXPORTER_URL`，启动导出器并请求 `/metrics`。检查 `pg_up`，再将端点加入 Prometheus，确认目标状态为 UP。
