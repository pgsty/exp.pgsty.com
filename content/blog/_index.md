---
title: PIG Blog
url: /blog/
linkTitle: Blog
description: Release notes and project news
weight: 40
type: blog
sidebar_root_for: self
sidebar_root_link_self: true
# 根下拉里已经有「博客」这一项，文档树里不必再出现一次。
toc_root: true

outputs:
  - HTML
  - RSS
  - print
cascade:
  type: blog
  outputs:
    - HTML
    - print
  params:
    ui:
      sidebar_menu_foldable: false
      sidebar_menu_compact: false
      ul_show: 3
icon: fa-solid fa-blog
---

Release notes and project news for PIG — the PostgreSQL extension package manager by Pigsty.
