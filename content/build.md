---
title: "pig build"
description: "Build PostgreSQL extensions from source with pig build"
weight: 130
icon: fas fa-hammer
categories: [Reference]
---

The `pig build` command simplifies the full workflow for building PostgreSQL extensions from source. It provides build infrastructure setup, dependency management, and compilation environments for standard and custom PostgreSQL extensions across supported operating systems.

```bash
pig build - Build Postgres Extension

Environment Setup:
  pig build spec                   # init build spec and directory (~ext)
  pig build repo                   # init build repo (=repo set -ru)
  pig build repo --beta            # init build repo with PostgreSQL beta repo
  pig build tool  [mini|full|...]  # init build toolset
  pig build rust  [-y] [-m]        # install Rust toolchain
  pig build pgrx  [-v <ver>] [-b]  # install & init pgrx (0.19.1)
  pig build proxy [id@host:port ]  # init build proxy (optional)

Package Building:
  pig build pkg   [ext|pkg...]     # complete pipeline: get + dep + ext
  pig build get   [ext|pkg...]     # download extension source tarball
  pig build dep   [ext|pkg...]     # install extension build dependencies
  pig build ext   [ext|pkg...]     # build extension package

Quick Start:
  pig build spec                   # setup build spec and directory
  pig build pkg citus              # build citus extension
```

| Command | Description | Notes |
|:---|:---|:---|
| `build spec` | Initialize build specification directory | |
| `build repo` | Initialize required repositories | Requires sudo or root |
| `build tool` | Initialize build tools | Requires sudo or root |
| `build rust` | Install Rust toolchain | Requires sudo or root |
| `build pgrx` | Install and initialize pgrx | Requires sudo or root |
| `build proxy` | Initialize build proxy | |
| `build get` | Download source tarballs | |
| `build dep` | Install extension build dependencies | Requires sudo or root |
| `build ext` | Build extension packages | Requires sudo or root |
| `build pkg` | Complete pipeline: get, dep, ext | Requires sudo or root |
{.full-width}


## Quick Start

The fastest way to set up a build environment and build an extension:

```bash
# Step 1: initialize build specs
pig build spec

# Step 2: build an extension with the complete pipeline
pig build pkg citus

# Built packages will be placed under:
# - EL: ~/ext/pkg/ (also available via ~/rpmbuild/RPMS/)
# - Debian: ~/ext/pkg/ (also available via ~/debbuild/DEBS/)
```

For finer control:

```bash
# Environment setup
pig build spec                   # initialize build specs
pig build repo                   # configure repositories
pig build repo --beta            # configure repositories and add PostgreSQL 19 beta repo
pig build tool                   # install build tools
pig build tool --beta            # install build tools plus PG19 beta build packages

# Build steps
pig build get citus              # download source
pig build dep citus              # install dependencies
pig build ext citus              # build package

# Or run all three steps at once
pig build pkg citus              # get + dep + ext
```


## Build Infrastructure

### Directory Layout

```
~/ext/                           # real working directory
├── pkg/                         # built package output
├── src/                         # source tarball downloads
├── log/                         # build logs
└── tmp/                         # temporary files

~/rpmbuild/                      # EL build directory
├── RPMS -> ~/ext/pkg            # RPM output symlink
├── SOURCES -> ~/ext/src         # source symlink
├── SPECS/
├── BUILD/
├── BUILDROOT/
└── SRPMS/

~/debbuild/                      # Debian / Ubuntu build directory
├── DEBS -> ~/ext/pkg            # DEB output symlink
├── SOURCES -> ~/ext/src         # source symlink
├── SPECS/
└── BUILD/
```

**Build output locations:**

- **EL systems**: `~/ext/pkg/`, also accessible through `~/rpmbuild/RPMS/`
- **Debian systems**: `~/ext/pkg/`, also accessible through `~/debbuild/DEBS/`


## build spec

Set up build specifications and directory layout.

```bash
pig build spec                   # initialize ~/ext at the default location
pig build spec -f                # force re-download of the build spec tarball
pig build spec -m                # prefer the pigsty.cc China mirror
```

**What it does:**

1. Downloads the RPM or DEB build specification tarball.
2. Creates `~/ext/{pkg,src,log,tmp}` and the platform build directory.
3. Links `RPMS`/`DEBS` and `SOURCES` to `~/ext/pkg` and `~/ext/src`.
4. Syncs makefiles, specs, and Debian packaging files with incremental `rsync`.

**Working directory:** `~/ext/` stores sources, packages, logs, and temporary files. The platform packaging directory is `~/rpmbuild/` or `~/debbuild/`.


## build repo

Initialize package repositories required for building extensions.

```bash
pig build repo                   # equivalent to: pig repo set -ru
pig build repo -m                # use pigsty.cc mirror/proxy sources
pig build repo --beta            # also enable the PostgreSQL 19 beta repo module
```

**What it does:** initializes build repositories with `pig repo set -ru`: remove old repositories, add required repositories, and refresh package caches. `--beta/-b` appends the `beta` module for explicit PostgreSQL 19 beta builds; the stable default path still uses PG14-18.

**Options:**

- `-b|--beta`: additionally enable PostgreSQL beta repository modules
- `-m|--mirror`: prefer the `pigsty.cc` mirror/proxy sources


## build tool

Install development tools and compilers.

```bash
pig build tool                   # install default toolset
pig build tool mini              # minimal toolset
pig build tool full              # full toolset
pig build tool rust              # add Rust development tools
pig build tool --beta            # add PG19 beta build dependencies
```

**Toolsets:**

- **Minimal (`mini`)**: GCC/Clang compilers, Make, and generic build essentials; does not install PostgreSQL server/devel packages.
- **Default / `full`**: compilers, development libraries, packaging tools such as `rpmbuild` and `dpkg-dev`, plus stable PG14-18 build dependencies.
- **`--beta`**: additionally installs PG19 beta server/devel build packages on top of the default toolset.


## build rust

Install the Rust toolchain required by Rust-based extensions.

```bash
pig build rust                   # install with confirmation
pig build rust -y                # force reinstall Rust toolchain
pig build rust -m                # use China mirror mode and write Cargo mirror config
```

**Installed components:** Rust compiler (`rustc`), Cargo, Rust standard library, and development tools. `-m|--mirror` uses mirror mode and writes `rsproxy.cn` Cargo configuration.


## build pgrx

Install and initialize PGRX, the PostgreSQL extension framework for Rust.

```bash
pig build pgrx                   # install latest stable version (0.19.1)
pig build pgrx -v 0.19.1         # install a specific pgrx version
pig build pgrx --pg 18,17,16     # initialize pgrx for selected PG versions
pig build pgrx --pg init         # run cargo pgrx init without PG arguments
pig build pgrx -b                # include PostgreSQL 19 beta pg_config during auto-detection
```

**Prerequisites:** Rust toolchain and PostgreSQL development headers must be installed first. Default auto-detection only covers stable PG14-18; use `-b|--beta`, or explicitly pass `--pg 19`, when PG19 beta is required.


## build proxy

Configure a proxy for build environments with restricted internet access.

```bash
pig build proxy                  # interactive setup
pig build proxy user@host:8080   # use default local endpoint 127.0.0.1:12345
pig build proxy user@host:8080 127.0.0.1:1080
```


## build get

Download extension source tarballs.

```bash
pig build get citus              # single extension
pig build get citus pgvector     # multiple extensions
pig build get pdu pgdog          # use built-in source aliases
pig build get citus -f           # re-download even if the file already exists
pig build get citus -m           # prefer the pigsty.cc China mirror
```

Arguments to `pig build get` are extension names, package names, or source filenames. Unknown names are treated as source filenames. It does not expand `all` or `std` into built-in package sets; list the target package names explicitly for batch downloads.

Some source packages do not map directly to extension names, so `pig build get` includes special aliases for direct source downloads.

```bash
pig build get pdu                # download pdu-3.0.25.12.tar.gz
pig build get pgdog              # download pgdog-0.1.32.tar.gz
pig build get pgedge             # download both PostgreSQL and spock sources
pig build get onesparse          # download onesparse, graphblas, and lagraph
```

Common special source aliases include: `babelfishpg` / `babelfish`, `agensgraph` / `agentsgraph`, `oriolepg` / `orioledb`, `cloudberry`, `pgedge`, `pdu`, `pgdog`, `rdkit`, `onesparse`, and `libfepgutils`.


## build dep

Install dependencies required to build extensions.

```bash
pig build dep citus              # single extension
pig build dep citus pgvector     # multiple extensions
pig build dep citus --pg 17,16   # for selected PG versions
```

**Options:**

- `--pg`: specify one or more PostgreSQL major versions. If omitted, pig infers versions from extension metadata or local PostgreSQL installations.


## build ext

Compile extensions and create installation packages.

```bash
pig build ext citus              # build one extension
pig build ext citus pgvector     # build multiple extensions
pig build ext citus --pg 17      # build for a selected PG version
pig build ext citus -s           # include debug symbols (RPM only)
```

**Options:**

- `--pg`: specify one or more PostgreSQL major versions.
- `-s|--symbol`: build debug symbol packages (RPM only).


## build pkg

Run the complete build pipeline: download, dependency installation, and build.

```bash
pig build pkg citus              # build one extension
pig build pkg citus pgvector     # build multiple extensions
pig build pkg citus --pg 17,16   # build for multiple PG versions
pig build pkg citus -s           # include debug symbols
pig build pkg citus -m           # prefer the pigsty.cc China mirror for sources
```

**Options:**

- `--pg`: specify one or more PostgreSQL major versions.
- `-s|--symbol`: build debug symbol packages (RPM only).
- `-m|--mirror`: prefer the `pigsty.cc` mirror when downloading source files.


## Common Workflows

### Workflow 1: Build a Standard Extension

```bash
# 1. Set up the build environment once
pig build spec
pig build repo
pig build tool

# 2. Build the extension
pig build pkg pg_partman

# 3. Install the built package
sudo rpm -ivh ~/ext/pkg/pg_partman*.rpm  # EL
sudo dpkg -i ~/ext/pkg/*partman*.deb     # Debian
```

### Workflow 2: Build a Rust Extension

```bash
# 1. Set up Rust environment
pig build spec
pig build tool
pig build rust                   # add -y only if you need to force reinstall
pig build rust -m                # use mirror mode in China network environments
pig build pgrx

# 2. Build Rust extension
pig build pkg pgmq

# 3. Install
sudo pig ext add pgmq
```

### Workflow 3: Build Multiple Versions

```bash
# Build for multiple PostgreSQL versions
pig build pkg citus --pg 15,16,17

# Results in packages for each version:
# citus_15-*.rpm
# citus_16-*.rpm
# citus_17-*.rpm
```


## Troubleshooting

### Build Tools Not Found

```bash
# Install build tools
pig build tool

# For specific compiler sets
sudo dnf groupinstall "Development Tools"  # EL
sudo apt install build-essential          # Debian
```

### Missing Dependencies

```bash
# Install extension dependencies
pig build dep <extension>

# Check error messages for specific packages
# Install manually if needed
sudo dnf install <package>  # EL
sudo apt install <package>  # Debian
```

### PostgreSQL Headers Not Found

```bash
# Install PostgreSQL development package
sudo pig ext install pg18-devel

# Or specify pg_config path
export PG_CONFIG=/usr/pgsql-18/bin/pg_config
```

### Rust/PGRX Issues

```bash
# Reinstall Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Update PGRX
cargo install --locked cargo-pgrx@0.19.1

# Reinitialize PGRX
cargo pgrx init

# When PG19 beta is required
pig build repo --beta
pig build tool --beta
pig build pgrx -b
```


## Extension Build Matrix

### Common Extensions to Build

| Extension | Type | Build Time | Complexity | Special Requirements |
|:---|:---:|:---|:---|:---|
| pg_repack | C | Fast | Simple | None |
| pg_partman | SQL/PLPGSQL | Fast | Simple | None |
| citus | C | Medium | Medium | None |
| timescaledb | C | Slow | Complex | CMake |
| postgis | C | Very slow | Complex | GDAL, GEOS, Proj |
| pg_duckdb | C++ | Medium | Medium | C++17 compiler |
| pgroonga | C | Medium | Medium | Groonga libraries |
| pgvector | C | Fast | Simple | None |
| plpython3 | C | Medium | Medium | Python development |
| pgrx extensions | Rust | Slow | Complex | Rust, PGRX |
{.full-width}
