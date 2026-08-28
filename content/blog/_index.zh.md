---
title: "PG Exporter 博客"
url: /zh/blog/
linkTitle: "博客"
description: "pg_exporter 设计记录、发布注记与项目动态"
weight: 40
type: blog
sidebar_root_for: self
sidebar_root_link_self: true
toc_root: true
outputs: [HTML, RSS, print]
images: [img/pg_exporter.webp]
cascade:
  type: blog
  outputs: [HTML, print]
  images: [img/pg_exporter.webp]
  reading_time: true
  # 页尾分享条，只在博客生效。每一项都是普通的意图链接，仅携带本页永久链接与标题，
  # 没有 SDK、没有 iframe、没有第三方脚本、没有分享计数，外加一个本地复制按钮。
  share: [x, linkedin, reddit, hackernews, telegram, weibo, email, copy]
  params:
    sidebar_menu_foldable: false
    sidebar_menu_compact: false
    sidebar_expand_levels: 3
icon: fa-solid fa-blog
---

`pg_exporter` 的设计记录、发布注记与项目动态。它是一款声明式 PostgreSQL 与 PgBouncer 指标导出器。

在[设计归档](/zh/design/)中了解架构理由与被否决方案，或从[完整版本归档](/zh/release/)查看已经交付的变更。当前产品行为仍以[文档](/zh/docs/)为准。
