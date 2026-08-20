# PG Exporter Documentation on OINK

This repository is the OINK-based standalone bilingual
[PG Exporter](https://github.com/pgsty/pg_exporter) documentation site. It uses
Hugo Extended and the reusable [OINK](https://github.com/pgsty/oink) theme, with
English at `/` and Simplified Chinese at `/zh/`. Production builds pin OINK
`v0.5.0` in `go.mod`.

- Site: <https://exp.pgsty.com>
- Product source: <https://github.com/pgsty/pg_exporter>
- Theme source: <https://github.com/pgsty/oink>
- Latest stable release documented: `v1.4.1`

## Content layout

Documentation pages live at the site root. `/docs/` is the documentation
overview; the actual pages are `/start/`, `/install/`, `/deploy/`, `/config/`,
`/api/`, and so on. Chinese translations use the same paths below `/zh/`.

```text
content/
  docs/_index.md              # documentation overview
  intro.md                    # architecture and execution model
  start.md                    # first working scrape
  download.md                 # choose, install, enable, verify
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

## Theme boundary

OINK owns the documentation and blog shell, composable homepage, navigation
tree, table of contents, language switcher, offline search, syntax highlighting,
print/Markdown outputs, content components, and footer. PG Exporter fills those
theme surfaces through configuration and content:

- `data/home/en.yaml` and `data/home/zh.yaml`: bilingual OINK homepage sections
- `data/footer/en.yaml` and `data/footer/zh.yaml`: bilingual OINK footer data
- `data/home/metrics.yaml`: traceability ledger for homepage product facts
- `assets/scss/_variables_project.scss`: supported brand design tokens
- `assets/scss/_styles_project.scss`: narrow-screen anchor-offset correction for the OINK shell
- `layouts/404.html`: deterministic OINK-partial composition for the bilingual 404 output
- `layouts/robots.txt`: environment-aware crawler policy

The homepage uses OINK's linked capability boards and its `system` typography
preset. The main Docs entry uses OINK's one-level navigation menu, and the
Command Palette projects Download, Docs, and Blog from that same menu while
adding a bilingual latest-release command and the shared page actions. The
bilingual quick start uses the automatically numbered `steps` component; the
download guide uses the `tabs` component, enhanced code blocks, and a native
`filetree` fence for installed paths. Release listings explicitly stay text-only so
35 version notes remain easy to scan instead of repeating one generic product
image on every row.

There is no local homepage, footer, search, or download layout. The pinned OINK
module supplies those implementations; the sibling checkout provides the latest
theme during local migration QA.

The sole project-style rule restores the theme's own full navbar offset below
the `md` breakpoint. The OINK shell otherwise places deep-linked manual headings
behind its 56px sticky mobile subnav, and that offset is not exposed through
theme configuration or homepage data.

The 404 template is the sole local page layout. It composes OINK's public head,
navbar, footer, script, and translation partials because the theme's block-only
404 template can inherit either the document or print base during concurrent
multilingual, multi-output builds. Keeping the complete outer frame here makes
`404.html` deterministic without forking any theme component implementation.

Because the manuals intentionally remain physical root-level content files,
`data/docs_nav.json` supplies their hierarchy to OINK without moving them under
`content/docs/` or overriding the theme's sidebar templates.

The local `layouts/` directory should therefore remain minimal. Do not copy an
OINK layout into this site merely to restyle it; prefer theme configuration,
data-driven homepage sections, native content components, and supported Sass
variables first.

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

The standalone pages in this repository add architecture, compatibility,
security, troubleshooting, collector inventory, development, and release-history
corrections. Do not overwrite them with old content from the former demo site.

## Local development

Install Hugo Extended, Go, and Git. For theme development and migration QA,
keep the OINK checkout beside this directory:

```text
~/pgsty/
├── oink/
└── exp.pgsty.com/
```

`make d` (or `make dev`) applies a one-command replacement that points Hugo at
the sibling theme checkout without creating `go.work`. It does not pin the preview port, and no Node.js
toolchain or CDN is required:

```bash
make d
```

Build the static output with the pinned remote theme using `make b`. Run the
strict, reproducible acceptance gate with:

```bash
make c
```

The gate disables workspace replacement, verifies `go.sum`, treats all Hugo path
and translation warnings as fatal, checks Markdown source/render hygiene, and
validates rendered internal links. Use `make check-local` to run the same site
checks against an in-progress sibling OINK checkout. `make s` is the short form
of the pinned production-environment preview; the long targets remain available.

## Publishing caution

The canonical Git remote is `git@github.com:pgsty/exp.pgsty.com.git`. Before any
push or deployment, verify that target together with the Pages project, custom
domain, and pinned OINK revision. Never publish this site through the historical
copied `pig.pgsty.com` remote.

## License

Unless otherwise noted, the original documentation text and site-specific
content in this repository are licensed under the
[Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)
(CC BY 4.0). When sharing or adapting that material, credit the PG Exporter
Contributors, link to the license and this documentation site, and indicate
whether changes were made. The complete legal code is in [LICENSE](LICENSE).

This content license does not relicense the OINK theme, PG Exporter software,
project names or trademarks, or third-party assets. Those retain their own
licenses and terms.
