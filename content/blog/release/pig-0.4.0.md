---
title: "pig v0.4.0"
linkTitle: "v0.4.0"
date: 2025-05-01
author: "Ruohang Feng"
description: "do & pt sub-cmd, halo & orioledb"
categories: [release]
tags: [Release, pig]
weight: 290
---

- Updated extension list, available extensions reached **407**
- Added `pig do` subcommand for executing Pigsty playbook tasks
- Added `pig pt` subcommand for wrapping Patroni command-line tools
- Added extension aliases: `openhalo` and `orioledb`
- Added `gitlab-ce` / `gitlab-ee` repository distinction
- Built with the latest Go 1.24.2 and upgraded dependency versions
- Fixed `pig ext status` panic issue under specific conditions
- Fixed `pig ext scan` unable to match several extensions

Release: https://github.com/pgsty/pig/releases/tag/v0.4.0
