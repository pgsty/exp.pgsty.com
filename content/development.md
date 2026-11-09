---
title: "Development"
linkTitle: "Development"
description: "Build and test pg_exporter, author collectors, regenerate configs, and understand the release pipeline"
weight: 120
icon: fa-solid fa-code-branch
categories: [Guide]
---

PG Exporter keeps SQL and metric definitions in YAML. The Go runtime loads those definitions, collects results, and serves HTTP requests. Start a change in the layer that owns the behavior.

Stable **v{{< param version >}}** is the reference for the user manuals. The separate `snort` development branch contains experimental Composite, Patroni, pgBackRest, and PostgreSQL log features; they are absent from `main` and v1.6.0. Their contracts and status are recorded in [Design](/design/).

## Repository Layout {#repository-layout}

| Path | Purpose |
|:---|:---|
| `exporter/` | CLI parsing, URL/config loading, planning, execution, metrics, health state, HTTP handlers, tests |
| `config/` | 57 collector files and one schema reference for PostgreSQL 10–19 and PgBouncer |
| `pg_exporter.yml` | Generated monolithic default config (`make conf`) |
| `legacy/config/` | Collector definitions for PostgreSQL 9.1-9.6 |
| `legacy/pg_exporter.yml` | Generated legacy monolithic config (`make conf9`) |
| [Design Records](/design/) | Canonical rationale, rejected alternatives, invariants, and dated release boundaries |
| `monitor/` | Grafana dashboards and database initialization helper |
| `package/` | systemd environment/unit files and package scripts |
| `.goreleaser.yml` | Cross-platform archives, RPM/DEB packages, checksums, Docker images, and GitHub Release |
{.full-width}

## Toolchain {#toolchain}

The v1.6.0 tag declares Go **1.27.3**. Use the toolchain required by the revision you build. To build the stable tag:

```bash
git clone --branch v{{< param version >}} https://github.com/pgsty/pg_exporter.git
cd pg_exporter
go mod download
make build
./pg_exporter --version
```

`make build` and GoReleaser both inject version, branch, revision, and build-date
metadata. Release artifacts disable CGO. A branch build can retain the fallback
release version, so check its revision as well as `--version`.

For a code change, create a working branch from the intended source revision. Read
`AGENTS.md` and inspect `git status --short --branch` before editing.

## Test Before and After a Change {#test-before-and-after-a-change}

```bash
go mod tidy -diff
go test -race -count=1 ./...
GODEBUG=httpmuxgo121=1 go test -count=1 ./...
go vet ./...
```

Configuration tests cover PostgreSQL and PgBouncer branch selection, legacy
collectors, generated-file consistency, metric names, labels, predicates, and
snapshot histograms. Runtime tests cover concurrent scrapes, reloads, and HTTP
handlers. SQL compatibility also requires running the query as the monitoring
role on each affected database version.

For runtime changes, cross-build the six release targets: Linux amd64/arm64/ppc64le,
Darwin amd64/arm64, and Windows amd64. The existing helper is:

```bash
make goreleaser-build
```

This command installs GoReleaser if needed and rebuilds the snapshot output in
`dist/`. Keep binaries, packages, and release archives outside Git.

## Change or Add a Collector {#change-or-add-a-collector}

1. Choose the numeric group and a unique top-level branch name.
2. Set `name` to the stable metric namespace when multiple version/role branches should emit one metric family.
3. Write SQL with an explicit result-column list.
4. Add `min_version` / `max_version`, role tags, fact tags, and predicates as narrowly as required.
5. Declare every returned column exactly once under `metrics`.
6. Pick `ttl`, `timeout`, `fatal`, and `skip` based on operational cost and failure impact.
7. Run config tests, regenerate the merged file, and inspect the diff.
8. Test the query as the monitoring role against every relevant server version and role.
9. Update [Bundled Collectors](/collectors/) and the affected manual for public metric changes. Add release notes when the version ships.

Read `config/0000-doc.yml` in the same source revision as the change. The current
[configuration manual](/config/) explains the stable schema.

Record public contract or architecture decisions in the companion repository’s
bilingual [Design Records](/design/). State the source revision, decision,
alternatives, and delivery status. Keep unreleased behavior marked as such until a
tag and artifacts ship. Small code-local fixes need tests and the relevant manual
update, not a new design article.

### Column rules {#column-rules}

- `LABEL` becomes a Prometheus label; avoid unbounded or sensitive values.
- `GAUGE` is for values that can move in either direction.
- `COUNTER` is for monotonically increasing source values (resets still occur on server restart/stat reset).
- `HISTOGRAM` builds a snapshot distribution from SQL rows. Its `_bucket`, `_count`, and `_sum` series are gauges that may decrease; do not apply `rate()` or `increase()`.
- `DISCARD` ignores a result column without exporting it.
- `rename`, `default`, and `scale` change the emitted name/value semantics and need compatibility review.

`le` is reserved when a collector contains a histogram. Metric and label names are validated while loading the configuration so invalid names fail before scraping.

## Regenerate Configs {#regenerate-configs}

```bash
make conf     # config/*.yml -> pg_exporter.yml
make conf9    # legacy/config/*.yml -> legacy/pg_exporter.yml

git diff -- pg_exporter.yml legacy/pg_exporter.yml
```

These two generated YAML files are tracked in Git. CI checks them against the
ordered source files. Edit the source fragments, regenerate the YAML, and include
both in the change.

## Exercise a Collector Locally {#exercise-a-collector-locally}

```bash
# Syntax/schema only; no target required
./pg_exporter --config=./config --dry-run

# Build a target-specific plan and exit
PG_EXPORTER_URL='postgres://monitor@localhost/postgres' \
  ./pg_exporter --config=./config --explain --fail-fast

# Run, inspect the plan and observe timing/errors
PG_EXPORTER_URL='postgres://monitor@localhost/postgres' \
  ./pg_exporter --config=./config --log.level=debug
# Run the following in another terminal.
curl -fsS localhost:9630/metrics >/dev/null
curl -fsS localhost:9630/explain
curl -fsS localhost:9630/stat
```

`--explain` selects collectors but does not execute their SQL. Exercise the
metrics endpoint to test results and permissions. Test populated and zero-row
results. A missing configured `LABEL` or `HISTOGRAM` column rejects the
whole collector result in either case.

For cached or optional components, also test the disabled path, failure isolation,
reload, and shutdown. For persistent log state, cover restart, rotation,
truncation, partial records, and state-file permissions.

## Release Pipeline {#release-pipeline}

GoReleaser produces:

- Linux, macOS, and Windows archives;
- RPM and DEB packages;
- SHA256 `checksums.txt`;
- amd64/arm64 Docker images and multi-architecture manifests;
- a GitHub Release for the tag.

Before tagging, align `exporter.Version`, the Makefile version, package metadata,
and release documentation. After the release workflow finishes, verify archive
and package checksums, the container manifest, and the binary’s build revision.
Then update this site’s `params.version`, download checksums, landing-page
version data, manuals, and the relevant Design record.

A local snapshot build checks packaging without publishing a release. Use the
release workflow for tagged artifacts and verify the installed version separately
after deployment.

## Documentation Workflow {#documentation-workflow}

Work on this site in the companion `exp.pgsty.com` repository. Edit paired English
and Chinese pages, then run:

```bash
make check
```

This builds the site with strict warnings and checks Markdown and internal links.
Review both rendered languages, especially commands, tables, and mobile overflow.

The import script can refresh `install`, `deploy`, `config`, `api`, and release
history from the Pigsty manuals. Generate into a temporary directory first so the
import does not overwrite site-specific edits:

```bash
preview_dir=$(mktemp -d)
python3 bin/sync_pg_exporter_content.py \
  --pigsty-io ../pigsty.io \
  --pigsty-cc ../pigsty.cc \
  --output "$preview_dir"
```

Compare the generated files with `content/` and apply the relevant changes. Keep
the standalone guides and Design archive authored here.

PG Exporter source contributions use [Apache 2.0](https://github.com/pgsty/pg_exporter/blob/v1.6.0/LICENSE).
This site’s original documentation uses [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Submit software changes to [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter)
and documentation changes to [pgsty/exp.pgsty.com](https://github.com/pgsty/exp.pgsty.com).
