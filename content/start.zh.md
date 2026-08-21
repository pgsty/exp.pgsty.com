---
title: "快速上手"
linkTitle: "快速上手"
description: "五分钟内运行 PG Exporter 并把 PostgreSQL 指标暴露给 Prometheus"
weight: 20
icon: fa-solid fa-rocket
categories: [参考]
search_keywords: [快速上手, 安装, 监控用户, pg_monitor, dry-run, pg_up, 抓取, Prometheus, explain, stat]
search_boost: 1.5
layout: landing
landing: start
---

<!-- 落地页布局渲染的是 data/landing/start/<lang>.yaml，而不是这段正文。
     下面这段是本页的可检索文本：OINK 的离线索引会跳过没有原始正文的页面。 -->

安装 PG Exporter，在目标 PostgreSQL 实例上创建最小权限的 `pg_monitor` 角色，用
`PG_EXPORTER_URL` 把导出器指向它，先用 `pg_exporter --dry-run` 解析配置，再在 `:9630`
上启动。抓取 `/metrics` 得到 `pg_up 1`、`pg_version` 与 `pg_in_recovery`，说明整条链路
已经打通；随后把目标加入 Prometheus 抓取任务，并让抓取间隔大于采集器 TTL。出问题时，
`/explain` 给出每个采集器的规划结论，`/stat` 给出它的错误与耗时。
