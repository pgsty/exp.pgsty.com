---
title: "PIG Documentation"
linkTitle: "Docs"
description: "Install, manage, and build PostgreSQL and its extensions with the pig CLI."
weight: 1
type: docs
icon: fa-solid fa-book
# 根下拉已经把「文档」列为当前文档集，树里不必再出现一次。
toc_root: true
---

— **Postgres Install Genius, the missing extension package manager for the PostgreSQL ecosystem**

PIG is a command-line tool specifically designed for installing, managing, and building PostgreSQL and its extensions. Developed in Go, it is ready to use out of the box, simple, and lightweight (about 5 MB).
PIG is not a reinvented wheel, but rather a **PiggyBack** - a high-level abstraction layer that leverages existing Linux distribution package managers (`apt`/`dnf`).
It abstracts away the differences between operating systems, chip architectures, and PG major versions, allowing you to install and manage PG kernels and {{< param pgext_count >}} packaged extensions with just a few simple commands.

PIG is also automation-friendly by design: consistent parameter styles, clear error messages, preview switches like `--plan`, and confirmation steps.

Please note: for extension installation, **pig is not a mandatory component**. You can still use apt/dnf package managers to directly access the [**Pigsty PGSQL**](https://pigsty.io/docs/repo/pgsql/) repository.

- [**Introduction**](/intro/): Why do we need a dedicated PG package manager?
- [**Getting Started**](/start/): Quick start guide and examples
- [**Installation**](/install/): Download, install, and update pig


## Quick Start

Use the following command to [**install**](/install/) PIG on your system:

**Default Installation** (Cloudflare CDN):

```bash
curl -fsSL https://repo.pigsty.io/pig | bash
```

**China Mirror**:

```bash
curl -fsSL https://repo.pigsty.cc/pig | bash
```

After installation, you can [**get started**](/start/) with just a few commands. For example, to install PG 18 and the [**`pg_duckdb`**](https://pigsty.io/ext/e/pg_duckdb) extension:

```bash
$ pig repo set                        # One-time setup for Linux, Pigsty + PGDG repos (overwrites!)
$ pig install pg18                    # Install PostgreSQL 18 kernel (native PGDG packages)
$ pig install pg_duckdb -v 18         # Install pg_duckdb extension (for PG 18)
$ pig install -y postgis timescaledb  # Install multiple extensions for current active PG version
$ pig install -y vector               # You can use extension name (vector) or package name (pgvector)!
```


## Command Reference

Run `pig help <command>` to get detailed help for subcommands.

**Extension Management:**

- [**pig repo**](/repo/): Manage software repositories
- [**pig ext**](/ext/): Manage PG extensions
- [**pig build**](/build/): Build extensions from source
- [**pig install**](/cmd/#pig-install): Install PostgreSQL and extension packages through the native package manager

**Pigsty Management:**

- [**pig sty**](/sty/): Manage Pigsty installation and Grafana dashboards
- [**pig inventory**](/inventory/): Inspect, edit, validate, and exchange the Pigsty inventory
- [**pig context**](/cmd/#pig-context): Collect host, PostgreSQL, Patroni, pgBackRest, and extension context
- [**pig pg**](/pg/): Manage local PostgreSQL server
- [**pig pt**](/pt/): Run patronictl transparently to manage Patroni HA clusters
- [**pig pb**](/pb/): Manage pgBackRest backup & restore
- [**pig pitr**](/pitr/): Point-in-time recovery workflow


## About

The `pig` CLI tool is developed by [Vonng](https://vonng.com/en/) (rh@vonng.com) and is open-sourced under the [Apache 2.0](https://github.com/pgsty/pig/?tab=Apache-2.0-1-ov-file#readme) license.

You can also check out the [**PIGSTY**](https://pgsty.com) project, which provides a complete PostgreSQL RDS DBaaS experience including extension delivery.

- [**PGEXT**](https://github.com/pgsty/pgext): Extension data and management tools
- [**PIG**](https://github.com/pgsty/pig): PostgreSQL package manager
- [**PIGSTY**](https://github.com/pgsty/pigsty): Batteries-included PostgreSQL distribution
