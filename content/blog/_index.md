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
  params:
    ui:
      sidebar_menu_foldable: false
      sidebar_menu_compact: false
      ul_show: 3
icon: fa-solid fa-blog
---

Release notes and project updates for `pg_exporter`, the declarative PostgreSQL and pgBouncer metrics exporter.

Start with the [complete release archive](/release/) or return to the [documentation](/docs/).
