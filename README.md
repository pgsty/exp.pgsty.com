# PIG Documentation

This repository contains the bilingual website for **PIG** — *Postgres Install Genius*, the
PostgreSQL extension package manager by [Pigsty](https://pigsty.io). It is built with
[Hugo](https://gohugo.io/) and [Docsy](https://www.docsy.dev/), with English at `/` and
Simplified Chinese at `/zh/`.

- Site: <https://pig.pgsty.com>
- Project: <https://github.com/pgsty/pig>

## Layout

Documentation pages live at the **site root** — `/install/`, `/repo/`, `/pg/` — with no
`/docs/` path prefix. `/docs/` is only the documentation overview page, and the sidebar tree
is built from the top-level pages by front-matter `weight`.

```
content/
  _index.md            # landing page metadata (the page itself is layouts/index.html)
  docs/_index.md       # /docs/ — documentation overview, listed in the sidebar root menu
  start.md             # /start/      weight 10
  intro.md             # /intro/      weight 20
  install.md           # /install/    weight 30
  _link_release.md     # sidebar entry pointing at /release/ (manualLink, not a page)
  _div_cmd.md          # sidebar group heading (sidebar_divider, not a page)
  cmd.md               # /cmd/        weight 100
  repo.md ext.md build.md sty.md inventory.md pg.md pt.md pb.md pitr.md
  blog/                # /blog/ — all posts, newest first
    release/           # /release/ and /release/pig-X.Y.Z/
data/home/metrics.yaml # landing page counters
```

Blog URLs drop the `blog` prefix: `permalinks.page` and `permalinks.section` in
`hugo.yaml` use `:sections[1:]`, so `content/blog/release/pig-1.6.0.md` publishes at
`/release/pig-1.6.0/`. A new blog subsection is a new top-level prefix with no config
change. Only `content/blog/_index.md` pins its own `url: /blog/`, because slicing its
single section would resolve to `/`.

Release notes are one dated post per version under `content/blog/release/`. Adding a
release means adding a `pig-X.Y.Z.md` / `.zh.md` pair with `weight` ascending from the
newest.

Each page ships as an English `.md` plus a Chinese `.zh.md`. Two sections stay out of the
docs sidebar tree via `toc_root: true` — `docs/` and `blog/` — because the sidebar root
menu already lists them.

## Local development

Install Hugo Extended, Go, Node.js, and npm. Install the pinned PostCSS toolchain once,
then run the local server:

```bash
npm ci
make dev
```

Build the static site with:

```bash
make build
```

Run the module verification, warning-strict production build, and internal link check with:

```bash
make check
```

Docsy is pinned as a Hugo Module. Project-specific layouts and SCSS extend the theme
without vendoring its source.

## Writing conventions

- Every page ships as an English `.md` / Chinese `.zh.md` pair with aligned content.
- Do not set `url:` in front matter — the file path already produces the intended URL.
  Chinese pages get the `/zh/` prefix automatically.
- In-site links are written as absolute paths: `/install/` in English pages, `/zh/install/`
  in Chinese pages.
- Links into the rest of the Pigsty manual are absolute and language-specific:
  `https://pigsty.io/...` for English, `https://pigsty.cc/...` for Chinese.
- Command transcripts are real executions against the current `pig` binary; do not invent
  output.
- Version numbers come from site params, not from prose: `{{< param version >}}` is the
  `pig` version, `{{< param pigsty_version >}}` is the embedded Pigsty version, and
  `{{< param pgext_count >}}` is the packaged extension count. Keep them in sync with
  `internal/config/config.go` in the `pig` repository.
