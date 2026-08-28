---
title: "Development"
linkTitle: "Development"
description: "Build and test pg_exporter, author collectors, regenerate configs, and understand the release pipeline"
weight: 120
icon: fa-solid fa-code-branch
categories: [Guide]
---

The project intentionally keeps most monitoring logic in YAML and a smaller execution engine in Go. Changes therefore fall into two paths: collector work and exporter-runtime work. Both paths should keep the merged configs, tests, documentation, and release metadata aligned.

## Repository Layout

| Path | Purpose |
|:---|:---|
| `exporter/` | CLI parsing, URL/config loading, planning, execution, metrics, health state, HTTP handlers, tests |
| `config/` | 58 ordered collector definition files for PostgreSQL 10-19+ and PgBouncer |
| `pg_exporter.yml` | Generated monolithic default config (`make conf`) |
| `legacy/config/` | Collector definitions for PostgreSQL 9.1-9.6 |
| `legacy/pg_exporter.yml` | Generated legacy monolithic config (`make conf9`) |
| `docs/design/` | Authoritative design notes such as snapshot histogram semantics |
| `monitor/` | Grafana dashboards and database initialization helper |
| `package/` | systemd environment/unit files and package scripts |
| `.goreleaser.yml` | Cross-platform archives, RPM/DEB packages, checksums, Docker images, and GitHub Release |
{.full-width}

## Toolchain

The current `go.mod` declares Go **1.27.0**. For a normal development build:

```bash
git clone https://github.com/pgsty/pg_exporter.git
cd pg_exporter
go mod download
make build
./pg_exporter --version
```

The binary is built with CGO disabled for release artifacts. `make build` is suitable for local development; GoReleaser supplies version, branch, revision, and build-date metadata for official artifacts.

## Test Before and After a Change

```bash
go test ./...
go test -race ./...

# Confirm all supported PostgreSQL and PgBouncer branches remain coverable,
# and that config structure, metric names, labels, and histograms are valid.
go test ./exporter/...
```

The test suite includes config coverage through PostgreSQL 19, PostgreSQL 9 legacy coverage, concurrency/reload behavior, HTTP route validation, label and metric-name validation, predicate caching, and snapshot histogram acceptance.

For a runtime change, also cross-build the supported release targets or use:

```bash
make goreleaser-build
```

## Change or Add a Collector

1. Choose the numeric group and a unique top-level branch name.
2. Set `name` to the stable metric namespace when multiple version/role branches should emit one metric family.
3. Write SQL with an explicit result-column list.
4. Add `min_version` / `max_version`, role tags, fact tags, and predicates as narrowly as required.
5. Declare every returned column exactly once under `metrics`.
6. Pick `ttl`, `timeout`, `fatal`, and `skip` based on operational cost and failure impact.
7. Run config tests, regenerate the merged file, and inspect the diff.
8. Test the query as the monitoring role against every relevant server version and role.
9. Update [Bundled Collectors](/collectors/) and release notes when the public metric surface changes.

Use [`config/0000-doc.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0000-doc.yml) as the executable schema reference.

### Column rules

- `LABEL` becomes a Prometheus label; avoid unbounded or sensitive values.
- `GAUGE` is for values that can move in either direction.
- `COUNTER` is for monotonically increasing source values (resets still occur on server restart/stat reset).
- `HISTOGRAM` builds a snapshot distribution from SQL rows. Its `_bucket`, `_count`, and `_sum` series are gauges that may decrease; do not apply `rate()` or `increase()`.
- `DISCARD` validates/ignores a result column without exporting it.
- `rename`, `default`, and `scale` change the emitted name/value semantics and need compatibility review.

`le` is reserved when a collector contains a histogram. Metric and label names are validated while loading the configuration so invalid names fail before scraping.

## Regenerate Configs

```bash
make conf     # config/*.yml -> pg_exporter.yml
make conf9    # legacy/config/*.yml -> legacy/pg_exporter.yml

git diff -- pg_exporter.yml legacy/pg_exporter.yml
```

Generated files are committed artifacts. CI checks that they exactly match the ordered source files; never edit only the monolithic output.

## Exercise a Collector Locally

```bash
# Syntax/schema only; no target required
./pg_exporter --config=./config --dry-run

# Build a target-specific plan and exit
PG_EXPORTER_URL='postgres://monitor@localhost/postgres' \
  ./pg_exporter --config=./config --explain

# Run, inspect the plan and observe timing/errors
PG_EXPORTER_URL='postgres://monitor@localhost/postgres' \
  ./pg_exporter --config=./config --log.level=debug
curl localhost:9630/explain
curl localhost:9630/stat
```

Test zero-row results as well as populated results. Since v1.4.1, a missing configured `LABEL` column rejects the collector result atomically, including when the query happens to return no rows.

## Release Pipeline

GoReleaser produces:

- Linux, macOS, and Windows archives;
- RPM and DEB packages;
- SHA256 `checksums.txt`;
- amd64/arm64 Docker images and multi-architecture manifests;
- a GitHub Release for the tag.

The release version is injected into `exporter.Version`. Keep the fallback version, Makefile version, README badge, package metadata, and documentation parameter aligned before tagging. Validate the tag, Release object, checksums, package contents, container manifests, and install behavior as separate layers.

## Documentation Workflow

The standalone documentation repository can import the authoritative Pigsty module pages and split the consolidated history with:

```bash
python3 bin/sync_pg_exporter_content.py \
  --pigsty-io /path/to/pigsty.io \
  --pigsty-cc /path/to/pigsty.cc \
  --output ./content
```

The generated core pages are then supplemented by standalone-only guides such as this page, compatibility, security, collectors, and troubleshooting. Run the site warning-strict build and link checker before publishing.

Contributions are licensed under [Apache 2.0](https://github.com/pgsty/pg_exporter/blob/main/LICENSE). Open changes and issues at [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter).
