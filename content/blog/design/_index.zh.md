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

设计归档解释 PG Exporter 为什么采用今天的实现方式。每篇文章都会区分设计、实现、合并、发布、软件包、部署与生产验证，避免把一项已经接受的设计误读成已经发布的功能。

当前产品行为以[使用手册](/zh/docs/)为准，已经交付的版本以[发布归档](/zh/release/)为准；本栏目记录形成这些结果的理由、备选方案、不变量与验证证据。
