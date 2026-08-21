---
title: "Download PG Exporter"
linkTitle: "Download"
description: "Choose, install, configure, enable, and verify PG Exporter packages, archives, containers, Pigsty automation, or source builds"
weight: 25
icon: fa-solid fa-download
categories: [Guide]
search_keywords: [download, install, package, RPM, DEB, YUM, APT, container, Docker, binary, checksum, tarball, Pigsty, source]
search_boost: 1.5
layout: landing
landing: download
---

<!-- The landing layout renders `data/landing/download/<lang>.yaml`, not this
     body. The paragraph below is the page's searchable text: OINK's offline
     index skips a page with no raw content, and this page is a top-level
     navigation entry that readers look for by artifact name. -->

Install PG Exporter from the Pigsty APT or YUM repository, a pinned RPM or DEB
package, a release tarball for Linux, macOS, or Windows, the multi-architecture
`pgsty/pg_exporter` container image, Pigsty automation, or a source build of a
tagged release. Every route runs the same binary and the same declarative
collectors; every published artifact carries a SHA-256 digest. After installing,
create the monitoring role, provide the connection URL, run `pg_exporter
--dry-run`, confirm `pg_up 1` on `:9630/metrics`, and add the target to
Prometheus.
