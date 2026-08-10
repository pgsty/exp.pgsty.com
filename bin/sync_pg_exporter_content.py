#!/usr/bin/env python3
"""Import authoritative pg_exporter docs and split release history into posts.

The source sites remain the upstream editorial copies.  This script adapts
their front matter and internal links for the standalone exp.pgsty.com URL
layout, then creates one bilingual blog post for every repository tag.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


VERSIONS = [
    ("v1.4.1", "2026-07-29T21:31:19+08:00"),
    ("v1.4.0", "2026-07-18T10:41:26+08:00"),
    ("v1.3.0", "2026-06-24T12:04:24+08:00"),
    ("v1.2.2", "2026-04-14T20:09:59+08:00"),
    ("v1.2.1", "2026-03-21T09:23:31+08:00"),
    ("v1.2.0", "2026-02-12T19:37:24+08:00"),
    ("v1.1.2", "2026-01-15T23:06:15+08:00"),
    ("v1.1.1", "2025-12-31T00:03:31+08:00"),
    ("v1.1.0", "2025-12-15T14:09:58+08:00"),
    ("v1.0.3", "2025-11-20T17:19:38+08:00"),
    ("v1.0.2", "2025-08-14T13:12:49+08:00"),
    ("v1.0.1", "2025-07-17T09:15:40+08:00"),
    ("v1.0.0", "2025-05-06T23:43:42+08:00"),
    ("v0.9.0", "2025-04-26T23:12:49+08:00"),
    ("v0.8.1", "2025-03-29T12:33:55+08:00"),
    ("v0.8.0", "2025-02-14T15:40:25+08:00"),
    ("v0.7.1", "2024-12-29T17:00:02+08:00"),
    ("v0.7.0", "2024-08-13T19:41:28+08:00"),
    ("v0.6.1", "2024-01-26T17:26:17+08:00"),
    ("v0.6.0", "2023-10-18T12:54:49+08:00"),
    ("v0.5.0", "2022-04-28T07:27:37+08:00"),
    ("v0.4.1", "2022-03-08T18:48:00+08:00"),
    ("v0.4.0", "2021-07-12T16:09:02+08:00"),
    ("v0.3.2", "2021-02-01T11:12:06+08:00"),
    ("v0.3.1", "2020-12-04T17:27:21+08:00"),
    ("v0.3.0", "2020-10-29T16:47:32+08:00"),
    ("v0.2.0", "2020-03-21T19:10:25+08:00"),
    ("v0.1.2", "2020-02-20T15:12:29+08:00"),
    ("v0.1.1", "2020-01-10T01:30:28+08:00"),
    ("v0.1.0", "2020-01-08T21:10:42+08:00"),
    ("v0.0.5", "2020-01-08T20:12:11+08:00"),
    ("v0.0.4", "2019-12-20T17:22:44+08:00"),
    ("v0.0.3", "2019-12-14T00:03:23+08:00"),
    ("v0.0.2", "2019-12-09T20:43:23+08:00"),
    ("v0.0.1", "2019-12-09T14:12:22+08:00"),
]

TAG_ONLY = {"v0.0.1", "v0.0.5"}

DOCS = {
    "start": {
        "en": ("Getting Started", "Quick Start", "Get PG Exporter running and expose PostgreSQL metrics to Prometheus in five minutes", "fa-solid fa-rocket"),
        "zh": ("快速上手", "快速上手", "五分钟内启动 PG Exporter，并向 Prometheus 暴露 PostgreSQL 指标", "fa-solid fa-rocket"),
        "weight": 20,
    },
    "install": {
        "en": ("Installation", "Installation", "Install PG Exporter from packages, release archives, containers, Pigsty, or source", "fa-solid fa-cloud-arrow-down"),
        "zh": ("安装指南", "安装指南", "通过软件包、发布压缩包、容器、Pigsty 或源码安装 PG Exporter", "fa-solid fa-download"),
        "weight": 30,
    },
    "deploy": {
        "en": ("Production Deployment", "Deployment", "Run pg_exporter with systemd, Docker, or Kubernetes and connect it to Prometheus", "fa-solid fa-boxes-packing"),
        "zh": ("生产部署", "部署指南", "使用 systemd、Docker 或 Kubernetes 运行 pg_exporter 并接入 Prometheus", "fa-solid fa-server"),
        "weight": 50,
    },
    "config": {
        "en": ("Collector Configuration", "Configuration", "Complete reference for the declarative YAML collector format and execution model", "fa-solid fa-code"),
        "zh": ("采集器配置", "配置参考", "声明式 YAML 采集器格式与执行模型的完整参考", "fa-solid fa-code"),
        "weight": 90,
    },
    "api": {
        "en": ("HTTP API", "HTTP API", "Metrics, health, role-routing, reload, explain, statistics, and version endpoints", "fa-solid fa-plug"),
        "zh": ("HTTP API", "HTTP API", "指标、健康检查、角色路由、重载、解释、统计与版本端点", "fa-solid fa-plug"),
        "weight": 110,
    },
}

MANUAL_DESCRIPTIONS = {
    "en": {
        "v0.6.1": "Security dependency update plus connection-timeout and configuration-directory fixes",
        "v0.0.5": "Timeouts, fatal collectors, priority semantics, pg_up fixes, and per-collector documentation",
    },
    "zh": {
        "v0.6.1": "依赖安全更新，以及连接超时与配置目录修复",
        "v0.0.5": "新增超时、致命采集器与优先级语义，修复 pg_up 并补齐采集器文档",
    },
}

MANUAL_BODIES = {
    "en": {
        "v0.6.1": """## Changes

- Update `golang.org/x/net` from `v0.10.0` to `v0.17.0` to pick up security fixes ([#38](https://github.com/pgsty/pg_exporter/pull/38))
- Fix `connect-timeout` propagation ([#37](https://github.com/pgsty/pg_exporter/pull/37)), contributed by [@mouchar](https://github.com/mouchar)
- Recognize both `.yaml` and `.yml` files in a configuration directory ([#34](https://github.com/pgsty/pg_exporter/pull/34)), contributed by [@japinli](https://github.com/japinli)

## Checksums

The original release published MD5 checksums for its archives and packages:

```text
107a67ca74b1d6e7bbe773694a48f6ab  pg_exporter-v0.6.1.darwin-amd64.tar.gz
75b57566838c38092a9c45531c031561  pg_exporter-v0.6.1.darwin-arm64.tar.gz
9e55128671b31dd28d6bca3d0429de8f  pg_exporter-v0.6.1.linux-amd64.tar.gz
68a8b9537f6deb1773d8bea9182bd613  pg_exporter-v0.6.1.linux-arm64.tar.gz
0b0cd62c59cab6d1ab8772d820e599db  pg-exporter_0.6.1_amd64.deb
947126150b71081d0592d7f1fce0aaac  pg-exporter_0.6.1_arm64.deb
6a3608b965143441a5921d3017318146  pg_exporter-0.6.1-1.aarch64.rpm
b3c9f2edd28810cae81cd0edad9eae5d  pg_exporter-0.6.1-1.x86_64.rpm
```
""",
        "v0.0.5": """## Changes

- Add per-collector query timeouts
- Replace the earlier `skip_error` behavior with the `fatal` collector policy
- Revise collector priority semantics
- Fix the built-in `pg_up` metric
- Add documentation for each bundled collector

This historical version exists as a repository tag but was not published as a separate GitHub Release object.
""",
    },
    "zh": {
        "v0.6.1": """## 变更

- 将 `golang.org/x/net` 从 `v0.10.0` 升级到 `v0.17.0`，纳入安全修复（[#38](https://github.com/pgsty/pg_exporter/pull/38)）
- 修复 `connect-timeout` 传递问题（[#37](https://github.com/pgsty/pg_exporter/pull/37)），由 [@mouchar](https://github.com/mouchar) 贡献
- 配置目录同时识别 `.yaml` 与 `.yml` 文件（[#34](https://github.com/pgsty/pg_exporter/pull/34)），由 [@japinli](https://github.com/japinli) 贡献

## 校验和

原始 Release 为压缩包与软件包发布了 MD5 校验和：

```text
107a67ca74b1d6e7bbe773694a48f6ab  pg_exporter-v0.6.1.darwin-amd64.tar.gz
75b57566838c38092a9c45531c031561  pg_exporter-v0.6.1.darwin-arm64.tar.gz
9e55128671b31dd28d6bca3d0429de8f  pg_exporter-v0.6.1.linux-amd64.tar.gz
68a8b9537f6deb1773d8bea9182bd613  pg_exporter-v0.6.1.linux-arm64.tar.gz
0b0cd62c59cab6d1ab8772d820e599db  pg-exporter_0.6.1_amd64.deb
947126150b71081d0592d7f1fce0aaac  pg-exporter_0.6.1_arm64.deb
6a3608b965143441a5921d3017318146  pg_exporter-0.6.1-1.aarch64.rpm
b3c9f2edd28810cae81cd0edad9eae5d  pg_exporter-0.6.1-1.x86_64.rpm
```
""",
        "v0.0.5": """## 变更

- 为每个采集器查询增加超时控制
- 以 `fatal` 采集器策略替代早期的 `skip_error` 行为
- 调整采集器优先级语义
- 修复内置的 `pg_up` 指标
- 为每个内置采集器补充文档

这个早期版本只有仓库标签，没有单独发布为 GitHub Release。
""",
    },
}


def strip_front_matter(text: str) -> str:
    match = re.match(r"\A---\s*\n.*?\n---\s*\n", text, re.S)
    if not match:
        raise ValueError("missing YAML front matter")
    return text[match.end() :].lstrip()


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def normalize_markdown(text: str) -> str:
    """Remove source-site whitespace noise without changing fenced examples."""

    output: list[str] = []
    in_fence = False
    previous_blank = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        is_fence = line.lstrip().startswith(("```", "~~~"))
        if is_fence:
            output.append(line)
            in_fence = not in_fence
            previous_blank = False
        elif in_fence:
            output.append(line)
        elif not line:
            if not previous_blank:
                output.append("")
            previous_blank = True
        else:
            output.append(line)
            previous_blank = False
    return "\n".join(output).rstrip() + "\n"


def rewrite_links(text: str, language: str) -> str:
    prefix = "/zh" if language == "zh" else ""
    for slug in ("start", "install", "deploy", "config", "api", "release"):
        target = f"{prefix}/{slug}/"
        text = text.replace(f"/docs/pg_exporter/{slug}/", target)
        text = re.sub(rf"/docs/pg_exporter/{slug}(?=[)#\s])", target.rstrip("/"), text)
    text = text.replace("/docs/pg_exporter/", f"{prefix}/docs/")
    text = re.sub(r"/docs/pg_exporter(?=[)#\s])", f"{prefix}/docs", text)
    text = text.replace(f"{prefix}/install/#compatibility", f"{prefix}/compatibility/")
    text = text.replace(f"{prefix}/install/#兼容性", f"{prefix}/compatibility/")
    text = text.replace("https://github.com/Vonng/pg_exporter", "https://github.com/pgsty/pg_exporter")
    text = text.replace("sudo yum install -y pg_exporter", "sudo yum install -y pg-exporter")
    return text


def adapt_doc_body(text: str, slug: str, language: str) -> str:
    """Apply standalone-site content contracts that an upstream sync must retain."""

    text = text.replace("pgBouncer", "PgBouncer")
    text = text.replace("docker hub", "Docker Hub")
    text = text.replace("prebuilt docker images", "prebuilt Docker images")

    if slug == "api":
        current = VERSIONS[0][0]
        text = text.replace(
            f'pg_exporter_build_info{{version="{current}",',
            'pg_exporter_build_info{version="v{{< param version >}}",',
        )

    if slug == "install":
        old_lead = (
            "`pg_exporter` can be installed via Pigsty, YUM/APT repositories, GitHub release packages (RPM/DEB/Tarball), Docker images, or built from source — pick whichever fits your infrastructure."
            if language == "en"
            else "`pg_exporter` 可以通过 Pigsty、YUM/APT 仓库、GitHub 发布包（RPM/DEB/Tarball）、Docker 镜像或源码构建安装，按你的基础设施任选一种即可。"
        )
        new_lead = (
            "**PG Exporter** can be installed through Pigsty, YUM/APT repositories, GitHub release packages (RPM/DEB/Tarball), Docker images, or source. For a guided comparison with install, enable, and verification commands, start at [Download PG Exporter](/download/); this page remains the complete artifact reference."
            if language == "en"
            else "**PG Exporter** 可以通过 Pigsty、YUM/APT 仓库、GitHub 发布包（RPM/DEB/Tarball）、Docker 镜像或源码构建安装。若需要包含选择、安装、启用与验证命令的向导，请从[下载 PG Exporter](/zh/download/)开始；本页继续作为完整制品参考。"
        )
        if old_lead not in text:
            raise ValueError(f"unexpected {language} install introduction")
        text = text.replace(old_lead, new_lead, 1)

        current = VERSIONS[0][0]
        current_number = current.removeprefix("v")
        release_heading = (
            f"**{current} Release Files:**" if language == "en" else f"**{current} 发布文件：**"
        )
        block_start = text.find(release_heading)
        block_end = text.find("{{% alert", block_start)
        if block_start < 0 or block_end < 0:
            raise ValueError(f"unexpected {language} install release table")
        release_block = text[block_start:block_end]
        release_block = release_block.replace(current, "v{{< param version >}}")
        release_block = release_block.replace(current_number, "{{< param version >}}")
        text = text[:block_start] + release_block + text[block_end:]

    if slug != "start":
        return text

    headings = (
        [
            ("## Step 1: Install", "## Install {#install}"),
            ("## Step 2: Create a Monitoring User", "## Create a Monitoring User {#create-monitoring-user}"),
            ("## Step 3: Run and Verify", "## Run and Verify {#run-and-verify}"),
            ("## Step 4: Hook into Prometheus", "## Hook into Prometheus {#hook-into-prometheus}"),
        ]
        if language == "en"
        else [
            ("## 第 1 步：安装", "## 安装 {#安装}"),
            ("## 第 2 步：创建监控用户", "## 创建监控用户 {#创建监控用户}"),
            ("## 第 3 步：启动并验证", "## 启动并验证 {#启动并验证}"),
            ("## 第 4 步：接入 Prometheus", "## 接入 Prometheus {#接入-prometheus}"),
        ]
    )
    for source, target in headings:
        if source not in text:
            raise ValueError(f"unexpected {language} start heading: {source}")
        text = text.replace(source, target, 1)

    first_heading = headings[0][1]
    closing_heading = "## Troubleshooting" if language == "en" else "## 常见问题排查"
    if closing_heading not in text:
        raise ValueError(f"unexpected {language} start closing heading")
    text = text.replace(first_heading, "{{% steps %}}\n\n" + first_heading, 1)
    text = text.replace(closing_heading, "{{% /steps %}}\n\n" + closing_heading, 1)
    text = re.sub(r"(?m)^-{8,}\s*\n?", "", text)

    if language == "en":
        text = text.replace(
            "This page is the shortest path: install `pg_exporter`",
            "This page is the shortest path: install **PG Exporter**",
        )
        text = text.replace(
            "On Linux amd64 you can download the binary directly (for other platforms and RPM/DEB/Docker options, see the [Installation guide](/install/)):",
            "On Linux amd64 you can download the binary directly. For managed packages, other platforms, containers, Pigsty, and source builds, use the [download guide](/download/).",
        )
        text = text.replace("superuser like `postgres`", "superuser such as `postgres`")
    else:
        text = text.replace(
            "本页是一条最短路径：安装 `pg_exporter`",
            "本页是一条最短路径：安装 **PG Exporter**",
        )
        text = text.replace(
            "Linux amd64 可以直接下载二进制（其他平台与 RPM/DEB/Docker 安装方式见 [安装指南](/zh/install/)）：",
            "Linux amd64 可以直接下载二进制。托管软件包、其他平台、容器、Pigsty 与源码构建方式参见[下载指南](/zh/download/)。",
        )
        text = text.replace("你需要准备的东西只有两样", "你只需要准备两样东西")
        text = text.replace("如果你只是在本机以", "如果只是在本机用")
        text = text.replace("请参阅 [兼容性说明]", "请参阅[兼容性说明]")
        text = text.replace("或到 [在线演示]", "或到[在线演示]")
        text = text.replace(") 看实际效果", ")查看实际效果")

    current = VERSIONS[0][0]
    text = text.replace(f"# pg_exporter {current} (", "# pg_exporter v{{< param version >}} (")
    return text


def import_docs(source: Path, output: Path, language: str) -> None:
    suffix = ".zh.md" if language == "zh" else ".md"
    for slug, meta in DOCS.items():
        title, link_title, description, icon = meta[language]
        body = strip_front_matter((source / f"{slug}.md").read_text(encoding="utf-8"))
        body = rewrite_links(body, language)
        body = adapt_doc_body(body, slug, language)
        front_matter = (
            "---\n"
            f"title: {yaml_string(title)}\n"
            f"linkTitle: {yaml_string(link_title)}\n"
            f"description: {yaml_string(description)}\n"
            f"weight: {meta['weight']}\n"
            f"icon: {icon}\n"
            f"categories: [{('参考' if language == 'zh' else 'Reference')}]\n"
            "---\n\n"
        )
        (output / f"{slug}{suffix}").write_text(
            normalize_markdown(front_matter + body), encoding="utf-8"
        )


def release_summaries(text: str) -> dict[str, str]:
    summaries: dict[str, str] = {}
    pattern = re.compile(
        r"^\|\s*\[(v\d+\.\d+\.\d+)\]\([^)]*\)\s*\|\s*[^|]+\|\s*([^|]+?)\s*\|",
        re.M,
    )
    for version, summary in pattern.findall(text):
        summary = re.sub(r"\s+", " ", summary).strip()
        summaries[version] = summary.replace("DockerHub", "Docker Hub").replace(
            "dockerhub", "Docker Hub"
        )
    return summaries


def release_sections(text: str) -> dict[str, str]:
    body = strip_front_matter(text)
    matches = list(re.finditer(r"^## (v\d+\.\d+\.\d+)\s*$", body, re.M))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        section = body[start:end].strip()
        section = re.sub(r"\n+[-]{8,}\s*$", "", section).strip()
        sections[match.group(1)] = section
    return sections


def normalize_release_body(body: str, version: str, language: str) -> str:
    body = body.replace("https://github.com/Vonng/pg_exporter", "https://github.com/pgsty/pg_exporter")
    body = body.replace("pgBouncer", "PgBouncer")
    body = body.replace("DockerHub", "Docker Hub").replace("dockerhub", "Docker Hub")
    body = body.replace("Add pgbouncer mode", "Add PgBouncer mode")
    body = body.replace("support pgbouncer v1.16", "support PgBouncer v1.16")
    body = body.replace(
        "Fix pgbouncer version parsing message level",
        "Fix PgBouncer version parsing message level",
    )
    if version == "v0.6.0":
        if language == "en":
            body = body.replace(
                "- Security Enhancement: Fix [security](https://github.com/pgsty/pg_exporter/security/dependabot?q=is%3Aclosed)\n  dependent-bot issue",
                "- Security enhancement: update dependencies to address reported vulnerabilities",
            )
        else:
            body = body.replace(
                "- 安全增强：修复 [安全](https://github.com/pgsty/pg_exporter/security/dependabot?q=is%3Aclosed) dependabot 问题",
                "- 安全增强：更新依赖，修复已报告的依赖漏洞",
            )
    body = re.sub(
        rf"\n?https://github\.com/pgsty/pg_exporter/releases/tag/{re.escape(version)}\s*$",
        "",
        body.strip(),
    ).strip()

    lines: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence:
            heading = re.fullmatch(r"\*\*(.+?)(?::|：)?\*\*", line.strip())
            if heading:
                label = heading.group(1).rstrip(":：")
                line = f"## {label}"
        lines.append(line)
    body = "\n".join(lines).strip()

    if not re.search(r"^##\s+", body, re.M):
        body = ("## 变更" if language == "zh" else "## Changes") + "\n\n" + body

    if version in TAG_ONLY:
        note = (
            "> 这是一个只有 Git 标签、没有独立 GitHub Release 对象的早期版本；本文依据标签提交与历史汇总文档归档。"
            if language == "zh"
            else "> This is an early repository tag without a separate GitHub Release object. This archival note is based on the tag commit and historical release summary."
        )
        resources = (
            f"## 版本资源\n\n- [查看 `{version}` 标签源码](https://github.com/pgsty/pg_exporter/tree/{version})"
            if language == "zh"
            else f"## Release resources\n\n- [Browse the `{version}` source tag](https://github.com/pgsty/pg_exporter/tree/{version})"
        )
        body = note + "\n\n" + body + "\n\n" + resources
    else:
        resources = (
            f"## 版本资源\n\n- [GitHub Release](https://github.com/pgsty/pg_exporter/releases/tag/{version})\n- [查看 `{version}` 标签源码](https://github.com/pgsty/pg_exporter/tree/{version})"
            if language == "zh"
            else f"## Release resources\n\n- [GitHub Release](https://github.com/pgsty/pg_exporter/releases/tag/{version})\n- [Browse the `{version}` source tag](https://github.com/pgsty/pg_exporter/tree/{version})"
        )
        body = body + "\n\n" + resources
    return body.rstrip() + "\n"


def import_releases(source: Path, output: Path, language: str) -> None:
    source_text = (source / "release.md").read_text(encoding="utf-8")
    summaries = release_summaries(source_text)
    summaries.update(MANUAL_DESCRIPTIONS[language])
    sections = release_sections(source_text)
    sections.update(MANUAL_BODIES[language])

    expected = {version for version, _ in VERSIONS}
    if set(summaries) != expected:
        missing = sorted(expected - set(summaries))
        extra = sorted(set(summaries) - expected)
        raise ValueError(f"release summary mismatch: missing={missing}, extra={extra}")
    if set(sections) != expected:
        missing = sorted(expected - set(sections))
        extra = sorted(set(sections) - expected)
        raise ValueError(f"release section mismatch: missing={missing}, extra={extra}")

    release_dir = output / "blog" / "release"
    release_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".zh.md" if language == "zh" else ".md"
    for index, (version, date) in enumerate(VERSIONS, start=1):
        front_matter = (
            "---\n"
            f"title: {yaml_string(f'PG Exporter {version}')}\n"
            f"linkTitle: {yaml_string(version)}\n"
            f"date: {yaml_string(date)}\n"
            'author: "Ruohang Feng"\n'
            f"description: {yaml_string(summaries[version])}\n"
            "categories: [release]\n"
            "tags: [Release, pg_exporter]\n"
            f"weight: {index * 10}\n"
            "---\n\n"
        )
        body = normalize_release_body(sections[version], version, language)
        (release_dir / f"{version}{suffix}").write_text(
            normalize_markdown(front_matter + body), encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pigsty-io", type=Path, required=True, help="pigsty.io repository root")
    parser.add_argument("--pigsty-cc", type=Path, required=True, help="pigsty.cc repository root")
    parser.add_argument("--output", type=Path, required=True, help="standalone site content directory")
    args = parser.parse_args()

    en_source = args.pigsty_io / "content" / "docs" / "pg_exporter"
    zh_source = args.pigsty_cc / "content" / "docs" / "pg_exporter"
    args.output.mkdir(parents=True, exist_ok=True)

    import_docs(en_source, args.output, "en")
    import_docs(zh_source, args.output, "zh")
    import_releases(en_source, args.output, "en")
    import_releases(zh_source, args.output, "zh")

    print(f"generated {len(DOCS) * 2} docs and {len(VERSIONS) * 2} release posts")


if __name__ == "__main__":
    main()
