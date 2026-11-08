---
title: "Container Trust Roots and Release Checks"
linkTitle: "Container Trust"
date: "2026-11-08T00:00:00+08:00"
lastmod: "2026-11-08T00:00:00+08:00"
authors: [Vonng]
categories: [design]
tags: [Design, Security, Compatibility]
summary: "Unreleased: include CA roots and the license in both scratch images, and exercise TLS and DEB artifacts in release validation."
---

> **Status:** Implemented but unreleased.<br>
> **Decision date / last verification:** 2026-11-08 / 2026-11-08.<br>
> **Scope:** Container and release-validation changes based on v1.5.0 source `1891254`, incorporating the packaging correction from `68c95ba`. No exporter runtime or driver change.<br>
> **Delivery:** Source is committed locally as `370b9fa`; the companion record is committed locally. Both Docker build paths, amd64/arm64 GoReleaser images, three DEB architectures, Go tests, static checks, and the documentation build are validated. Push, tag, published packages/images, deployment, and production verification have not occurred for this change.

## Problem

Both v1.5.0 Docker build paths end at `scratch` without a system CA bundle. The ordinary Dockerfile also omits `LICENSE`; the GoReleaser Dockerfile already includes it. An OCI license label identifies the license but does not carry its text.

The current `lib/pq` driver uses Go's system trust roots when `sslrootcert` is omitted. A container without roots cannot verify a publicly trusted server certificate in `verify-ca` or `verify-full` mode. The [v1.5.0 target-state record](/design/target-state-contracts/) correctly documents the previous need to mount a CA.

## Decision and invariants

Keep the final image based on `scratch`. Copy the distribution CA bundle to `/etc/ssl/certs/ca-certificates.crt`, a standard Go trust-store location, and include `/LICENSE` in both build paths. The source build obtains roots from its Go builder; the release build installs `ca-certificates` in a separate Alpine stage and copies only the bundle into the final image. The Docker build-context allowlist must admit `LICENSE`.

This supplies public trust roots; it does not enable TLS automatically. Omitted `sslmode` still becomes `disable`. Use `sslmode=verify-full` to verify both the chain and hostname. Private CAs still require a mounted file selected by `sslrootcert`. No private key or organization-specific root belongs in the published image.

Roots are fixed at image build time, so CA updates require rebuilding and distributing the image. Runtime package installation, a shell, driver migration, mutual TLS changes, and changes to the default TLS mode are outside this decision.

## Alternatives

Requiring every deployment to mount public roots retains the packaging gap and complicates ordinary verified connections. Switching the final image to a complete Linux distribution adds runtime files unnecessary for this static binary. Copying the CA bundle preserves the existing container shape while supplying the missing runtime data.

## Acceptance and release boundaries

CI builds the source Dockerfile. The release test builds the actual GoReleaser snapshot, including amd64 and arm64 Docker images, without publishing it. Both paths run the same image checks:

- Compare the image's license and default configuration with the source files, parse its CA bundle, and execute its binary.
- Connect to a disposable PostgreSQL TLS server using `verify-ca` and `verify-full`. An unknown private CA must fail; an explicit trusted CA must succeed.
- Append the test CA to the image's bundle through a temporary mount and verify system-root lookup without `sslrootcert`. Reject a mismatched hostname under `verify-full`.

The TLS cases use a local server and generated certificates, without depending on a public TLS endpoint. They verify bundle parsing and trust-store lookup, not every public CA or the full mutual TLS matrix.

Release artifact checks retain RPM compatibility assertions and add DEB metadata, payload, configuration modes, conffiles, and installation checks. All DEB architectures are inspected; the container's native architecture is installed and its binary runs as `prometheus`. Checksums must verify successfully.

These gates validate a build candidate. Stable documentation and release notes must continue to describe v1.5.0 until a new tag and its artifacts actually ship this correction.
