---
title: Ruohang Feng
linkTitle: Vonng
description: Author of PG Exporter and Pigsty; PostgreSQL infrastructure, monitoring, and the tooling in between.
---

Ruohang Feng ([@Vonng](https://github.com/Vonng)) writes **PG Exporter** and
[Pigsty](https://pigsty.io/), the PostgreSQL distribution it was built for.

PG Exporter started from a practical complaint: the metric definitions that
matter to a database engineer were locked inside an exporter binary, where the
people who understand the database could neither read them nor change them.
Moving them into YAML and SQL made the metric contract reviewable, and made
version, role, and extension differences something the exporter decides at
runtime instead of something a release note apologises for.

- [pigsty.io](https://pigsty.io/) — the PostgreSQL distribution this exporter ships with
- [@Vonng on GitHub](https://github.com/Vonng) — the repositories behind these projects
- [vonng.com](https://vonng.com/en) — long-form writing
