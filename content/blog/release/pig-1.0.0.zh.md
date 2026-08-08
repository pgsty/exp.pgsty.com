---
title: "pig v1.0.0"
linkTitle: "v1.0.0"
date: 2026-01-26
author: "冯若航"
description: "444, 新增 pg/pt/pb/pitr 子命令，可用性矩阵"
categories: [release]
tags: [Release, pig]
weight: 150
---

本版本引入三组主要的新子命令（`pig pg`、`pig pt`、`pig pb`），用于管理 PostgreSQL、Patroni 和 pgBackRest，同时新增编排式 PITR 命令，并增强扩展可用性显示。

## 新增命令

- `pig pg` - PostgreSQL 实例管理
  - `pg init/start/stop/restart/reload/status` - 控制与管理 PostgreSQL 实例
  - `pg role/promote` - 检测和切换实例角色（主库/从库）
  - `pg psql/ps/kill` - 连接与会话管理
  - `pg vacuum/analyze/freeze/repack` - 数据库维护操作
  - `pg log` - 日志查看（list/tail/cat/less）

- `pig pt` - Patroni 集群管理
  - `pt list/config` - 查看集群状态与配置
  - `pt restart/reload/reinit` - 管理集群成员
  - `pt switchover/failover` - 集群切换操作
  - `pt pause/resume` - 控制自动故障切换
  - `pt start/stop/status/log` - Patroni 服务管理

- `pig pb` - pgBackRest 备份管理
  - `pb info/ls` - 查看备份信息
  - `pb backup/restore/expire` - 备份操作
  - `pb create/upgrade/delete` - Stanza 管理
  - `pb check/start/stop/log` - 控制操作

- `pig pitr` - 编排式时间点恢复
  - 自动协调 Patroni/PostgreSQL
  - 多种恢复目标：时间、LSN、XID、还原点
  - 支持计划预览模式与恢复后指引

## 新功能

- 为 `pig ext avail` 和 `pig ext ls` 添加可用性矩阵

## 改进

- 统一 pg/pt/pb 命令别名风格
- 规范化错误消息格式
- 代码重构与清理

## Bug 修复

- 修复 UTIL 扩展分类缺失问题

## 校验和

```bash
306637079e942bcac9ccbc089cd09a80051898f8db1630269bb1acd3fbdaa872  pig-1.0.0-1.aarch64.rpm
d2b9440410f00efbca174d63b507c39d97fc55f402d8e9290ee054c1b1c6414c  pig-1.0.0-1.x86_64.rpm
c8a169e48a8168ee03db508ca2edc22b56ecf6997bae924e9023796ab7ae4e62  pig-v1.0.0.darwin-amd64.tar.gz
c0996037bfeffeae241b545e69d46c06e7fec2d7d456885229f3af9a7f9ea2f8  pig-v1.0.0.darwin-arm64.tar.gz
13837c6f2379edf965888bad9e373e69f70cb72e8428bca18c2c804e2bd879f6  pig-v1.0.0.linux-amd64.tar.gz
08207dfedd6f72745631596a3d3293de65cc12e1544956a643d1da2165d2c876  pig-v1.0.0.linux-arm64.tar.gz
a543882aa905713a0c50088d4e848951b6957a37a1594d7e9f3fe46453d5ce66  pig_1.0.0-1_amd64.deb
4cd6ec54261b09025c12e9c56bcc0cd3c11779ea0e8becdbd4f901cf2e7c8995  pig_1.0.0-1_arm64.deb
```

发布：https://github.com/pgsty/pig/releases/tag/v1.0.0
