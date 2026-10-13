---
title: "PG Exporter 博客"
url: /zh/blog/
linkTitle: "博客"
description: "pg_exporter 博客原文、设计记录、发布注记与项目动态"
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

PG Exporter 的实践文章、设计决策与发布注记。

[文章](/zh/article/)介绍监控实践，[设计记录](/zh/design/)解释架构与取舍，[发布注记](/zh/release/)列出各版本变更。安装和运行当前稳定版，请查阅[使用手册](/zh/docs/)。
