---
title: "PG Exporter Blog"
url: /blog/
linkTitle: "Blog"
description: "Release notes and project updates for pg_exporter"
weight: 40
type: blog
sidebar_root_for: self
sidebar_root_link_self: true
toc_root: true
outputs: [HTML, RSS, print]
cascade:
  type: blog
  outputs: [HTML, print]
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

Release notes and project updates for `pg_exporter`, the declarative PostgreSQL and PgBouncer metrics exporter.

Start with the [complete release archive](/release/) or return to the [documentation](/docs/).
