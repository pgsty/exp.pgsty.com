---
title: "发布注记"
linkTitle: "发布注记"
description: "pg_exporter 每个仓库标签对应一篇双语发布注记"
weight: 30
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

归档覆盖从 `v0.0.1` 到 `v{{< param version >}}` 的全部 **35 个仓库标签**，每个版本各有一篇中英文注记。

其中 33 个版本有 GitHub Release；`v0.0.1` 和 `v0.0.5` 仅有 Git 标签。日期采用 GitHub 发布时间，标签版本采用提交时间，统一为 Asia/Shanghai（`UTC+08:00`）。

当前软件包和安装命令见[下载页](/zh/download/)。
