# PG Exporter Documentation on OINK

This repository is the OINK-based standalone bilingual
[PG Exporter](https://github.com/pgsty/pg_exporter) documentation site. It uses
Hugo Extended and the reusable [OINK](https://github.com/pgsty/oink) theme, with
English at `/` and Simplified Chinese at `/zh/`. Production builds pin OINK
to the exact version in `go.mod`.

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
  start.md                    # landing page: first working scrape
  download.md                 # landing page: choose, install, enable, verify
  install.md                  # packages, archives, containers, source
  compatibility.md            # target and artifact matrix
  deploy.md                   # production deployment
  security.md                 # database and HTTP hardening
  troubleshooting.md          # symptom-driven runbook
  config.md                   # complete collector schema
  collectors.md               # all 58 bundled definition files
  api.md                      # HTTP API
  development.md              # build, test, collector, release workflow
  authors/vonng/_index.md     # author taxonomy profile, with its portrait
  blog/design/*.md            # bilingual, dated design and decision records
  blog/release/vX.Y.Z.md      # one post per Git tag
```

`/start/` and `/download/` are OINK landing pages rather than manual pages:
their front matter carries `layout: landing` plus a `landing:` key, and the
sections come from `data/landing/<key>/<lang>.yaml`. Their Markdown bodies are
never rendered; they exist because OINK's offline index skips a page with no
raw content, and both pages are navigation entries readers search for.

Every English `.md` page has a `.zh.md` peer. Blog content stays under
`content/blog/`, but its public URL drops the `blog` component: for example,
`content/blog/release/v1.4.1.md` publishes at `/release/v1.4.1/`, while
`content/blog/design/snapshot-histograms.md` publishes at
`/design/snapshot-histograms/`.

## Theme boundary

OINK owns the documentation and blog shell, composable homepage, navigation
tree, table of contents, language switcher, offline search, syntax highlighting,
print/Markdown outputs, content components, and footer. PG Exporter fills those
theme surfaces through configuration and content:

- `data/home/en.yaml` and `data/home/zh.yaml`: bilingual OINK homepage sections
- `data/landing/download/{en,zh}.yaml` and `data/landing/start/{en,zh}.yaml`: the two landing pages
- `data/download/pg-exporter.yaml`: the install channels and release assets both landing pages and the `download` shortcode read
- `data/footer/en.yaml` and `data/footer/zh.yaml`: bilingual OINK footer data
- `data/home/metrics.yaml`: traceability ledger for product facts repeated in page data
- `assets/scss/_variables_project.scss`: supported brand design tokens
- `assets/scss/_styles_project.scss`: narrow-screen anchor-offset correction, and one gap between a download tab's glyph and its label
- `layouts/_partials/pgx/content-section.html`: content scope for landing sections that carry authored content
- `layouts/404.html`: deterministic OINK-partial composition for the bilingual 404 output
- `layouts/robots.txt`: environment-aware crawler policy

The homepage uses OINK's linked capability boards and its `system` typography
preset, and its hero carries the generated architecture diagram (see below).
The main Docs entry uses OINK's one-level navigation menu, and the Command
Palette projects Download, Docs, and Blog from that same menu while adding a
bilingual latest-release command and the shared page actions. The documentation
overview uses the native `{.cards}` link-list form; the manuals use the `tabs`
component, enhanced code blocks, and native `filetree` fences.

`/download/` and `/start/` are composed from OINK's landing sections, so neither
page needs a bespoke template, stylesheet, or runtime. `/download/` is
deliberately short — hero, install matrix, where to go next — because the matrix
already answers the question the page exists for; it is the theme's `download`
section reading `data/download/pg-exporter.yaml`, which is also where the
release assets table and its SHA-256 digests come from. `/start/` is the longer
one: an overview `steps` row, four `markdown` procedure sections carrying the
fragment ids other pages link to, a `code-plate` showing a healthy first scrape,
and a `faq` for the four common failures.

Page comments come from GitHub Discussions on this repository through giscus,
in the Announcements category, with one thread per page path so an English page
and its Chinese peer stay separate. They render wherever OINK renders a page end
— documentation, blog, and section indexes — and therefore not on the three
landing pages; front matter `comments: false` opts a page out. The frame is
lazy, so reading a page requests nothing from `giscus.app` until the reader
reaches the end of it.

The blog declares the `authors` taxonomy, a page-end share bar, and reading
time. The Design archive keeps dated rationale, rejected alternatives,
invariants, and explicit implementation/release boundaries; it is the canonical
replacement for source-repository `docs/design/` files. The release archive
publishes the compact `blog_index: table` form with
the reader-side toggle enabled, and the whole section reads immersively:
`featured_image: hero`, no sidebar, a `toc_style: flow` rail with no term
clouds. Each note carries `release_url` and closes with `{{< release-card >}}`,
so its links are derived from that one URL rather than hand-written.

The Blog, Design, and Release front matter cascades provide section-specific
fallback images (`pg_exporter.webp`, `pg_exporter-design.webp`, and
`pg_exporter-release.webp`). A page-bundle featured image or an explicit
page-level `images` value still wins, while `images: []` opts one page out.

There is no local homepage, footer, search, or download layout. The pinned OINK
module supplies those implementations; the sibling checkout provides the latest
theme during local migration QA.

Two project-style rules exist. The first restores the theme's own full navbar
offset below the `md` breakpoint, because the OINK shell otherwise places
deep-linked manual headings behind its 56px sticky mobile subnav. The second
adds the missing gap between a download tab's Font Awesome glyph and the channel
name it precedes. Neither is exposed through theme configuration.

`layouts/_partials/pgx/content-section.html` is a landing-section wrapper, not a
copy of one. OINK styles its content components — the enhanced code block above
all — under `.td-content`, which the landing shell does not establish, so a
`markdown`, `download`, or `faq` section renders those components unframed. The
wrapper emits that scope and then calls the theme's own section partial;
landing data selects it with `partial: pgx/content-section`.

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

The [Design Records](https://exp.pgsty.com/design/) are authoritative for why a
decision was made and what alternatives were rejected. Their visible status
blocks prevent an implemented-but-unreleased or superseded design from
overriding current manuals and release artifacts. New design guidance is
written here in bilingual form; the source repository keeps only short links
to the canonical article.

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
`start` is not imported: the Quick Start is a site-authored landing page.

## Generated images

```bash
python3 bin/build_architecture_diagram.py
```

This writes the four homepage hero diagrams — English and Chinese, light and
dark — to `static/img/architecture*.svg`. The OINK hero paints its media as two
CSS background images, one per colour scheme, so a bilingual site needs four
files; the geometry, the palettes, and both languages' copy live in the script
so they cannot drift. Its facts come from the `pg_exporter` source tree
(`exporter/arg.go`, `patroni.go`, `pgbackrest.go`): PostgreSQL over libpq,
PgBouncer through its admin console, Patroni through its own Prometheus
endpoint, pgBackRest by running the local CLI, all merged on `:9630/metrics`.

The three site-owned Blog fallback images are checked-in WebP assets under
`static/img/`: `pg_exporter.webp`, `pg_exporter-design.webp`, and
`pg_exporter-release.webp`.

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
