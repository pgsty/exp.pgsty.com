---
title: "pig v0.4.0"
linkTitle: "v0.4.0"
date: 2025-05-01
author: "冯若航"
description: "do 和 pt 子命令，halo 和 orioledb"
categories: [release]
tags: [Release, pig]
weight: 290
---

- 更新扩展列表，可用扩展达到 **407** 个
- 添加 `pig do` 子命令用于执行 Pigsty playbook 任务
- 添加 `pig pt` 子命令用于包装 Patroni 命令行工具
- 添加扩展别名：`openhalo` 和 `orioledb`
- 添加 `gitlab-ce` / `gitlab-ee` 仓库区分
- 使用最新 Go 1.24.2 构建并升级依赖项版本
- 修复特定条件下 `pig ext status` 的 panic 问题
- 修复 `pig ext scan` 无法匹配多个扩展的问题

发布：https://github.com/pgsty/pig/releases/tag/v0.4.0
