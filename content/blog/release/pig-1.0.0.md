---
title: "pig v1.0.0"
linkTitle: "v1.0.0"
date: 2026-01-26
author: "Ruohang Feng"
description: "New pg/pt/pb/pitr commands, availability matrix"
categories: [release]
tags: [Release, pig]
weight: 150
---

This release introduces three major new subcommand groups (`pig pg`, `pig pt`, `pig pb`) for managing PostgreSQL, Patroni, and pgBackRest, along with an orchestrated PITR command and enhanced extension availability display.

## New Commands

- `pig pg` - PostgreSQL instance management
  - `pg init/start/stop/restart/reload/status` - Control and manage PostgreSQL instances
  - `pg role/promote` - Detect and switch instance role (primary/replica)
  - `pg psql/ps/kill` - Connection and session management
  - `pg vacuum/analyze/freeze/repack` - Database maintenance operations
  - `pg log` - Log viewing (`list/tail/cat/less`)

- `pig pt` - Patroni cluster management
  - `pt list/config` - View cluster status and configuration
  - `pt restart/reload/reinit` - Manage cluster members
  - `pt switchover/failover` - Cluster failover operations
  - `pt pause/resume` - Control automatic failover
  - `pt start/stop/status/log` - Patroni service management

- `pig pb` - pgBackRest backup management
  - `pb info/ls` - View backup information
  - `pb backup/restore/expire` - Backup operations
  - `pb create/upgrade/delete` - Stanza management
  - `pb check/start/stop/log` - Control operations

- `pig pitr` - Orchestrated Point-In-Time Recovery
  - Automatic Patroni/PostgreSQL coordination
  - Multiple recovery targets: time, LSN, XID, restore point
  - Dry-run mode and post-recovery guidance

## New Features

- Add availability matrix to `pig ext avail` and `pig ext ls`

## Improvements

- Unified command aliases across pg/pt/pb commands
- Standardized error message format
- Code refactoring and cleanup

## Bug Fixes

- Fix missing UTIL extension category

## Checksums

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

Release: https://github.com/pgsty/pig/releases/tag/v1.0.0
