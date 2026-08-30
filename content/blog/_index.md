---
title: "PG Exporter Blog"
url: /blog/
linkTitle: "Blog"
description: "Original articles, design records, release notes, and project updates for pg_exporter"
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
  # The page-end share bar, scoped to the blog. Every entry is a plain intent
  # link carrying only this page's permalink and title -- no SDK, no iframe, no
  # third-party script, no share counts -- plus one local copy button.
  share: [x, linkedin, reddit, hackernews, telegram, weibo, email, copy]
  params:
    sidebar_menu_foldable: false
    sidebar_menu_compact: false
    sidebar_expand_levels: 3
icon: fa-solid fa-blog
---

Original long-form articles, design records, release notes, and project updates for `pg_exporter`, the declarative PostgreSQL and PgBouncer metrics exporter.

Read the [original articles](/article/) in full, including their original figures; use the [Design Records](/design/) for architectural reasoning and rejected alternatives, or scan the [complete release archive](/release/) for shipped changes. Current product behavior remains in the [documentation](/docs/).
