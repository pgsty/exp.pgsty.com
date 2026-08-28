---
title: "发布注记"
linkTitle: "发布注记"
description: "pg_exporter 每个仓库标签对应一篇双语发布注记"
weight: 10
icon: fa-solid fa-clipboard-list
# 归档采用紧凑表格形式：35 篇注记是用来扫读的，不是用来翻页的。
# blog_index_toggle 让行列表与卡片形式仍然只差一次点击。
blog_index: table
# 整个板块采用沉浸式阅读：由板块配图铺开的通栏封面、无侧边栏，以及不带术语云的
# 随文目录栏。索引页自己携带这些键（cascade 从不作用于声明它的页面），
# 并把同一套配方传给下面的每一篇注记。
images: [img/pg_exporter-release.webp]
featured_image: hero
sidebar_enabled: false
toc_taxonomies: false
cascade:
  images: [img/pg_exporter-release.webp]
  featured_image: hero
  toc_style: flow
  toc_taxonomies: false
  sidebar_enabled: false
---

这里按时间倒序收录 `pg_exporter` 的每个仓库标签：从 `v0.0.1` 到 `v{{< param version >}}`，共 **35 个标签版本**，每个版本一篇文章。

GitHub 当前有 33 个正式 Release 对象；`v0.0.1` 与 `v0.0.5` 两个仅有标签的早期版本也作为历史归档保留，并在文章内明确标注。存在 Release 时使用 GitHub 发布时间，否则使用源码标签时间，统一换算为 Asia/Shanghai（`UTC+08:00`）。

当前产物请从[最新 GitHub Release](https://github.com/pgsty/pg_exporter/releases/latest)下载；软件仓库、归档包、容器、Pigsty 与源码构建方式参见[下载指南](/zh/download/)。
