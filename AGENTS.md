# AGENTS.md

`exp.pgsty.com` is the standalone bilingual PG Exporter documentation site
(Hugo + the OINK theme). Read these project conventions before editing it.

`CLAUDE.md` is a compatibility symlink to this file. Edit `AGENTS.md`; never
replace the symlink with a copied, divergent instruction file.

## Start with the real repository state

- Run `git status --short --branch`, inspect `git branch -vv`, and identify the
  intended content and commit boundary before editing. Preserve unrelated dirty
  theme, dependency, homepage, and generated-output changes.
- For product claims, inspect the exact `pg_exporter` source revision and the
  latest stable tag separately. A development checkout may contain implemented
  but unreleased behavior.
- Reuse the OINK content model already present. Do not solve an editorial task
  by copying theme layouts or adding a site-local runtime.
- Treat source editing, local build, commit, push, hosted deployment, and public
  rendering as separate gates.

## URL and content conventions

- Documentation pages live at the root: `/download/`, `/install/`, `/config/`, `/api/`.
  `/docs/` is only the overview page. Do not move the manuals into
  `content/docs/` or add a `/docs/` prefix to their URLs.
- `/download/` and `/start/` are OINK landing pages, not manual pages. Their
  front matter is `layout: landing` plus `landing: <key>`, and their sections
  live in `data/landing/<key>/{en,zh}.yaml`. Their Markdown bodies are never
  rendered and exist only so OINK's offline index does not skip them; keep that
  text an accurate summary of the page. `/start/` keeps the section ids
  `install`, `create-monitoring-user`, `run-and-verify`, and
  `hook-into-prometheus` in both languages, because other pages link to them by
  fragment.
- `/download/` stays short on purpose: hero, install matrix, next steps. The
  matrix names each route's lifecycle owner and its commands, so a prose
  comparison in front of it and an activation checklist behind it were both
  restating it. Put a new download fact in `data/download/pg-exporter.yaml`
  rather than in a new section.
- Blog sources live under `content/blog/`, but public URLs omit `blog` through
  the Hugo permalink rule. `content/blog/release/v1.4.1.md` is
  `/release/v1.4.1/`; the Chinese peer is `/zh/release/v1.4.1/`.
- Design records live under `content/blog/design/` and publish at `/design/`
  plus `/zh/design/`. Do not add explicit `/blog/design/` URLs or recreate a
  `docs/design/` directory in the source repository.
- `content/_div_operate.*` and `content/_div_reference.*` are sidebar dividers,
  not pages. `content/_link_release.*` is the manual sidebar link to the release
  archive.
- English `.md` and Simplified Chinese `.zh.md` pages are maintained as pairs.
  Internal links use root-relative paths, with `/zh/` in Chinese content.

## Companion documentation model

This repository is not a copy of the source README. It is the companion
knowledge surface for humans and agents. Authority is split deliberately:

| Question | Authority |
| --- | --- |
| What does a particular binary or source revision do? | Exact `pg_exporter` source, tests, and artifact |
| What does the latest stable release support? | Stable tag/artifacts plus current manuals |
| How should a user install, configure, secure, or operate it? | Root-level manuals in this repository |
| Why was an architecture or compatibility decision made? | `content/blog/design/` |
| What shipped in a tagged version? | `content/blog/release/` plus the Git tag/Release |
| How does Pigsty embed PG Exporter? | Current Pigsty module and its upstream manuals |

The local sibling source is normally `../pg_exporter`. The upstream Pigsty
module manuals are normally:

- `../pigsty.io/content/docs/pg_exporter` (English)
- `../pigsty.cc/content/docs/pg_exporter` (Chinese)

A development source tree can justify an **Implemented but unreleased** Design
record. It must not silently rewrite stable manuals, download data, version
badges, or release notes as though a tag and artifacts already exist.

### Where new information belongs

Use the smallest correct surface:

| Information | Location |
| --- | --- |
| Architecture, public contract, failure semantics, compatibility choice, rejected alternative | `content/blog/design/<slug>.md` and `<slug>.zh.md` |
| Current user procedure or reference | Root-level paired manual such as `content/config.md` and `content/config.zh.md` |
| One tagged version's delivered changes | `content/blog/release/vX.Y.Z.md` and `.zh.md` |
| Homepage or landing-page product copy | `data/home/` or `data/landing/` |
| Download channel, artifact, or checksum | `data/download/pg-exporter.yaml` |
| Executable schema, code comment, fixture, or test-only explanation | The `pg_exporter` source repository |
| Raw agent prompt, private review transcript, local host log, or disposable experiment | Do not publish verbatim; extract the durable decision and evidence |

When design begins, create or update the Design record here rather than writing
a long-lived source-repository planning file. It may stay `draft: true` while
uncalibrated or private. Once safe to publish, the public route becomes the
canonical rationale link used by the source README, code comments, issues, and
pull requests.

Do not create a new record merely because another review occurred. Update the
existing record when the same decision evolves. Create a separate record when
the decision is independently reusable or supersedes an earlier direction.

### Design-record contract

Every record is an English/Chinese pair with matching decision date, status,
scope, flags, metric contracts, non-goals, and evidence. Use the date when the
decision crystallized; use `lastmod` for later calibration.

The visible opening block must identify:

- status: Proposed, Implemented but unreleased, Shipped, Rejected, or
  Superseded;
- decision date and last verification date;
- exact scope, version, tag, or source boundary;
- predecessor or replacement when one exists;
- which of implementation, merge, tag, package, deployment, and production
  verification have actually occurred.

The prose should make the record useful without the original chat or prompt:
context, decision, invariants, rejected alternatives, consequences, non-goals,
validation evidence, remaining gates, and authoritative references.

Before publication, remove local absolute paths, disposable host names or IPs,
secrets, raw agent prompts, model identities, transient command output, and
unverified market or legal claims. Retain exact metric names, flags, defaults,
limits, dates, and code/release boundaries after checking them against primary
sources.

Rejected and superseded records remain published because they explain why a
tempting path is absent. Mark them clearly and link to the replacement; never
rewrite an old article so it appears that the discarded direction never
existed.

### How to retrieve earlier design reasoning

Use this order:

1. Start at <https://exp.pgsty.com/design/> and read the visible status block,
   not only the title or publication date.
2. Search the editable sources locally:

   ```bash
   rg -n -i '<term>' content/blog/design
   git log --all -- content/blog/design
   ```

3. Use `git log --follow -- content/blog/design/<article>.md` for the evolution
   of one record, or `git log -S '<contract>' --all -- content/blog/design` for
   renamed and removed concepts.
4. Check `/release/` plus the corresponding source tag to determine what
   shipped. Check manuals plus source/tests to determine what is true now.
5. If an old source commit contains a deleted `docs/design/` file, treat it as
   archival evidence only. Reconstruct useful provenance here instead of
   restoring that directory as an authority.

### Cross-repository lifecycle

For a design-led source change:

1. Inspect dirty state and intended branches in both repositories.
2. Find and revise an existing record, or draft a new bilingual pair here.
3. Implement the source contract and keep code/tests and the article aligned.
4. Validate this site and the source independently.
5. Publish the Design route before replacing the last public source reference,
   or land coordinated commits without claiming deployment has happened.
6. After merge or release, update status and evidence rather than creating a
   contradictory second account.

The site build proves source/render integrity, not hosted deployment. Passing Go
tests proves an implementation candidate, not a tag, package, Pigsty rollout,
or production endpoint.

## Manual synchronization

`bin/sync_pg_exporter_content.py` imports `install`, `deploy`, `config`, and
`api`, rewrites `/docs/pg_exporter/...` links to the standalone URL layout, and
generates one release post per Git tag. Run it from the site root with all three
explicit path arguments shown in `README.md`.

The sync script does not own `content/blog/design/`. Never extend a mechanical
manual/release sync so it overwrites authored design history.

The manual pages `intro`, `compatibility`, `security`, `troubleshooting`,
`collectors`, and `development` are standalone-site extensions. Preserve their
extra detail during an upstream sync. `start` is deliberately not imported: the
Quick Start is a site-authored landing page, and importing the upstream manual
page would replace its front matter.

`bin/build_architecture_diagram.py` generates the four homepage hero diagrams
(English and Chinese, light and dark) into `static/img/`. Edit the script, never
the SVGs. Its facts come from the `pg_exporter` source tree, so re-read
`exporter/arg.go` and the sidecar collectors before changing a label.

## Release history

The archive contains one bilingual article per repository tag, newest first.
The current set is 35 tags from `v0.0.1` through `v1.4.1`. GitHub has 33 formal
Release objects; `v0.0.1` and `v0.0.5` are intentionally labeled as tag-only
history. Do not silently drop either case.

The current stable version comes from `params.version` in `hugo.yaml`; use
`{{< param version >}}` in prose where the latest version is intended. Historical
release articles keep their literal version numbers.

Each release note carries `authors: [Vonng]` and a `release_url`, and closes
with `{{< release-card >}}`; the card derives the release page, both source
archives, and the repository from that one URL. The card belongs at the end,
because a blog index row summarises a post from its rendered text and a leading
card would fill that summary with its own link labels.

Landing data cannot interpolate `params.version`. Version-derived facts written
into `data/landing/**` are recorded in `data/home/metrics.yaml`; a release bump
touches `params.version`, that ledger, and the checksums in
`data/download/pg-exporter.yaml`.

## Theme boundary

- OINK owns docs/blog layouts, navigation, TOC, search, language switching,
  blocks, and general content shortcodes. Configure or upgrade the theme rather
  than copying those implementation files into this site.
- The PG Exporter homepage uses OINK's native composable landing page. Product
  content lives in `data/home/en.yaml` and `data/home/zh.yaml`; do not add a
  local homepage layout, landing runtime, search dialog, or footer override.
- Keep local layout overrides minimal and list any new one in `README.md` with a
  concrete reason it cannot be expressed through OINK configuration or data.
  `layouts/_partials/pgx/content-section.html` is the only landing extension: it
  wraps a section in the theme's `.td-content` scope and then calls the theme's
  own section partial, because OINK styles its content components only inside
  that scope. Select it with `partial: pgx/content-section` in landing data;
  never reimplement a section.
- The install matrix, its commands, and its asset digests come from
  `data/download/pg-exporter.yaml`, which the `download` landing section and the
  `download` shortcode both read. Only a `pinned` channel may interpolate
  `${version}` and `${tag}`; any other `${...}` token is refused, so shell
  variables inside channel code use the brace-less form.
- The blog cascade in `content/blog/_index.*` declares the page-end share bar
  and reading time; the release section's own front matter declares the
  immersive recipe (`blog_index: table`, `featured_image: hero`,
  `sidebar_enabled: false`, `toc_style: flow`, `toc_taxonomies: false`) and
  cascades it to every note. The Blog, Design, and Release cascades use
  `static/img/pg_exporter.webp`, `pg_exporter-design.webp`, and
  `pg_exporter-release.webp` as their respective fallback images. Page-bundle
  images and explicit page-level `images` values still take priority. The
  three WebPs are site-owned assets and also provide the section-specific social
  image when an article has no image of its own.
- Comments are giscus over this repository's GitHub Discussions
  (`params.comments` in `hugo.yaml`). `repoId` and `categoryId` are GitHub node
  ids, not names: re-read them from the GraphQL API if the repository or the
  category changes. They render on every surface that has a page end and on none
  of the landing pages.
- Root-level manual hierarchy is declared in `data/docs_nav.json`; update both
  language-neutral URLs and active paths whenever a manual entry is added,
  removed, or regrouped.
- Local development uses a command-scoped module replacement for the sibling
  `../oink` checkout; published builds use the exact module revision in
  `go.mod` without generating a workspace file.

## Verification and publishing

- Run `make check` after content, template, CSS, JavaScript, or config changes.
  It performs a warning-strict Hugo build plus Markdown and internal-link checks.
- For design changes, also inspect the English and Chinese Blog/Design indexes,
  every changed article at desktop and narrow mobile widths, language switching,
  TOC, tables, code overflow, search, and the generated Markdown/LLMS outputs.
- Landing-page numbers displayed in the language home data mirror
  `data/home/metrics.yaml`; keep that traceability ledger aligned with the
  manual and current source tree.
- Do not treat a local Hugo build as a hosted deployment.
- Verify that the remote still targets the intended `exp.pgsty.com` repository
  before any push or deployment; never overwrite the PIG documentation
  repository.

## Documentation license

- Unless otherwise noted, original documentation text and site-specific content
  are licensed under CC BY 4.0. Keep the full legal code in `LICENSE`, the scope
  statement in `README.md`, and the visible footer notice aligned.
- The content license does not relicense OINK, PG Exporter software, trademarks,
  or third-party assets; preserve their own notices and licensing terms.
