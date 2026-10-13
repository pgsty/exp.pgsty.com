---
title: "设计归档"
linkTitle: "设计"
description: "PG Exporter 的架构决策、被否决方案与实现契约"
weight: 20
icon: fa-solid fa-pen-ruler
sidebar_expanded: true
blog_index: list
outputs: [HTML, RSS, print, markdown]
images: [img/pg_exporter-design.webp]
cascade:
  outputs: [HTML, print, markdown]
  images: [img/pg_exporter-design.webp]
---

设计记录解释 PG Exporter 的架构、备选方案与取舍。每篇注明状态、源码边界和最后核验日期。

快照直方图已随 v1.4.0 发布。Composite 模式、缓存 pgBackRest 指标和 PostgreSQL 日志指标已在开发分支实现，尚未进入稳定版 v{{< param version >}}。独立可观测性产品提案已被取代。

稳定版操作方法见[使用手册](/zh/docs/)，已发布变更见[发布归档](/zh/release/)。
