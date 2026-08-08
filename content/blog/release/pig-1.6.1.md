---
title: "pig v1.6.1"
linkTitle: "v1.6.1"
date: 2026-07-30
author: "Ruohang Feng"
description: "pig v1.6.1 refreshes the bundled extension catalog and aligns the embedded Pigsty version with 4.5.0."
categories: [release]
tags: [Release, pig]
weight: 10
---

`pig` v1.6.1 is a maintenance release on top of [v1.6.0](/release/pig-1.6.0/). It carries no new
commands and no flag changes — the point of the release is the catalog that ships inside the
binary.

## What changed

- **Extension catalog refreshed.** The embedded `extension.csv` is regenerated from the
  Pigsty package repositories, so `pig ext list` and `pig install` resolve against current
  package versions without a `pig ext reload` round trip.
- **Pigsty version aligned to 4.5.0.** The embedded Pigsty version that `pig sty` and
  `pig status` report now points at Pigsty 4.5.0.
- **Version strings bumped** across the build metadata and `pig update`.

The catalog still covers {{< param pgext_count >}} packaged extensions across PostgreSQL
14–18 on EL 8/9/10, Debian 12/13, and Ubuntu 22/24/26, for both `x86_64` and `aarch64`.

## Upgrading

```bash
pig update                 # upgrade in place through the native package manager
pig update -v 1.6.1        # or pin the exact version
```

A fresh install picks up v1.6.1 automatically:

```bash
curl -fsSL https://repo.pigsty.io/pig | bash   # global (Cloudflare CDN)
curl -fsSL https://repo.pigsty.cc/pig | bash   # mainland China mirror
```

You can also refresh only the catalog on an existing install, without upgrading the binary:

```bash
pig ext reload             # download the latest catalog to ~/.pig/extension.csv
```

See the [release notes](/release/) for the full version history, and the
[GitHub release page](https://github.com/pgsty/pig/releases/tag/v1.6.1) for artifacts and
checksums.
