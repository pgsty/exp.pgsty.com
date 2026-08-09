# PG Exporter Documentation

This repository contains the standalone bilingual site for
[PG Exporter](https://github.com/pgsty/pg_exporter), a declarative PostgreSQL and
PgBouncer metrics exporter for Prometheus. It uses Hugo Extended and Docsy, with
English at `/` and Simplified Chinese at `/zh/`.

- Site: <https://exp.pgsty.com>
- Project: <https://github.com/pgsty/pg_exporter>
- Latest stable release documented: `v1.4.1`

## Content layout

Documentation pages live at the site root. `/docs/` is the documentation overview;
the actual pages are `/start/`, `/install/`, `/deploy/`, `/config/`, `/api/`, and so
on. Chinese translations use the same paths below `/zh/`.

```text
content/
  docs/_index.md              # documentation overview
  intro.md                    # architecture and execution model
  start.md                    # first working scrape
  install.md                  # packages, archives, containers, source
  compatibility.md            # target and artifact matrix
  deploy.md                   # production deployment
  security.md                 # database and HTTP hardening
  troubleshooting.md          # symptom-driven runbook
  config.md                   # complete collector schema
  collectors.md               # all 58 bundled definition files
  api.md                      # HTTP API
  development.md              # build, test, collector, release workflow
  blog/release/vX.Y.Z.md      # one post per Git tag
```

Every English `.md` page has a `.zh.md` peer. Blog content stays under
`content/blog/`, but its public URL drops the `blog` component: for example,
`content/blog/release/v1.4.1.md` publishes at `/release/v1.4.1/`.

## Authoritative sources

The working product contract comes from the current
[`pgsty/pg_exporter`](https://github.com/pgsty/pg_exporter) source and the latest
stable release artifacts. The original module manuals are maintained at:

- English: `~/pgsty/pigsty.io/content/docs/pg_exporter`
- Chinese: `~/pgsty/pigsty.cc/content/docs/pg_exporter`

Use `bin/sync_pg_exporter_content.py` to import the five upstream manual pages,
rewrite their links for this standalone site, and split the combined release
history into one bilingual article per Git tag:

```bash
python3 bin/sync_pg_exporter_content.py \
  --pigsty-io ~/pgsty/pigsty.io/content/docs/pg_exporter \
  --pigsty-cc ~/pgsty/pigsty.cc/content/docs/pg_exporter \
  --output content
```

The standalone pages in this repository add architecture, compatibility, security,
troubleshooting, collector inventory, development, and release-history corrections.
Do not overwrite them with old content from the former demo site.

## Local development

Install Hugo Extended, Go, Node.js, and npm, then install the pinned PostCSS tools:

```bash
npm ci
make dev
```

Build the static output with `make build`. Run the strict acceptance gate with:

```bash
make check
```

The gate verifies Hugo modules, treats all Hugo path and translation warnings as
fatal, checks Markdown source/render hygiene, and validates rendered internal links.

## Publishing caution

This directory was copied from another site. Before enabling the included GitHub
Pages workflow, verify that `origin` points to the intended `exp.pgsty.com`
repository and that its Pages/custom-domain settings are correct. Never publish
this checkout through the copied `pig.pgsty.com` remote.
