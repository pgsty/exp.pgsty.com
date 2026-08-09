#!/usr/bin/env python3
"""Validate Markdown source hygiene and rendered Markdown residues.

The source pass is intentionally site-specific. It checks conventions that keep
Goldmark parsing deterministic without imposing generic rules that conflict with
Hugo features such as shortcodes, raw HTML, table attributes, or linkify.

Run this after Hugo has built the site so the rendered pass can also detect
Markdown delimiters that leaked into visible HTML instead of being parsed.
"""

from __future__ import annotations

import argparse
import html.parser
import pathlib
import re
import sys


FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(.*)$")
INLINE_CODE_RUN_RE = re.compile(r"`+")
STRONG_SPAN_RE = re.compile(
    r"(?<!\*)\*\*(?!\*)(?=\S)(.+?)(?<=\S)(?<!\*)\*\*(?!\*)"
)
ESCAPED_CHAR_RE = re.compile(r"\\.")
SKIP_HTML_TAGS = {"code", "kbd", "pre", "samp", "script", "style"}
RENDERED_MARKERS = {
    "strong marker": re.compile(r"(?<!\*)\*\*(?!\*)"),
    "underscore strong marker": re.compile(r"(?<!_)__(?!_)"),
    "inline link syntax": re.compile(r"!?\[[^\]\n]+\]\([^\n)]+\)"),
    "inline code marker": re.compile(r"`"),
    "Hugo shortcode": re.compile(r"\{\{[<%].*?[>%]\}\}"),
    "table delimiter": re.compile(r"\|\s*:?-{3,}:?\s*(?:\||$)"),
}


def mask_inline_markup(line: str) -> str:
    """Replace inline code spans and escaped characters while preserving offsets."""

    masked = list(line)
    runs = list(INLINE_CODE_RUN_RE.finditer(line))
    index = 0
    while index < len(runs):
        opener = runs[index]
        closer_index = next(
            (
                candidate
                for candidate in range(index + 1, len(runs))
                if len(runs[candidate].group()) == len(opener.group())
            ),
            None,
        )
        if closer_index is None:
            index += 1
            continue
        closer = runs[closer_index]
        masked[opener.start() : closer.end()] = " " * (closer.end() - opener.start())
        index = closer_index + 1

    for match in ESCAPED_CHAR_RE.finditer(line):
        masked[match.start() : match.end()] = " " * (match.end() - match.start())
    return "".join(masked)


def is_word_character(character: str) -> bool:
    """Return whether a delimiter needs whitespace from the adjacent character."""

    return character == "_" or character.isalnum()


def scan_source(path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        return [f"{path}: invalid UTF-8: {error}"]

    if not source.endswith("\n"):
        failures.append(f"{path}: missing final newline")
    if "\r" in source:
        failures.append(f"{path}: CR/CRLF line endings are not allowed")

    lines = source.splitlines()
    if not lines or lines[0].strip() != "---":
        failures.append(f"{path}:1: missing YAML front matter opener")
        body_start = 0
    else:
        front_matter_end = next(
            (index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"),
            None,
        )
        if front_matter_end is None:
            failures.append(f"{path}:1: unclosed YAML front matter")
            return failures
        body_start = front_matter_end + 1

    fence_character: str | None = None
    fence_length = 0
    fence_line = 0
    previous_blank = False

    for index, line in enumerate(lines):
        line_number = index + 1
        if line.rstrip(" \t") != line:
            failures.append(f"{path}:{line_number}: trailing whitespace")
        if "\t" in line:
            failures.append(f"{path}:{line_number}: tab character")
        if index < body_start:
            continue

        fence = FENCE_RE.match(line)
        if fence_character is not None:
            if (
                fence
                and fence.group(1)[0] == fence_character
                and len(fence.group(1)) >= fence_length
                and not fence.group(2).strip()
            ):
                fence_character = None
                fence_length = 0
                fence_line = 0
            previous_blank = False
            continue

        if fence:
            marker, info = fence.groups()
            fence_character = marker[0]
            fence_length = len(marker)
            fence_line = line_number
            if not info.strip():
                failures.append(f"{path}:{line_number}: fenced code block needs a language")
            previous_blank = False
            continue

        blank = not line.strip()
        if blank and previous_blank:
            failures.append(f"{path}:{line_number}: multiple consecutive blank lines")
        previous_blank = blank
        if blank:
            continue

        heading = HEADING_RE.match(line)
        if heading:
            suffix = heading.group(2)
            if suffix and not suffix.startswith(" "):
                failures.append(f"{path}:{line_number}: missing space after heading marker")
            elif suffix.startswith("  "):
                failures.append(f"{path}:{line_number}: multiple spaces after heading marker")
            if index > body_start and lines[index - 1].strip():
                failures.append(f"{path}:{line_number}: heading needs a blank line above")
            if index + 1 < len(lines) and lines[index + 1].strip():
                failures.append(f"{path}:{line_number}: heading needs a blank line below")

        prose = mask_inline_markup(line)
        for strong in STRONG_SPAN_RE.finditer(prose):
            before = prose[strong.start() - 1] if strong.start() else ""
            after = prose[strong.end()] if strong.end() < len(prose) else ""
            sides: list[str] = []
            if before and is_word_character(before):
                sides.append("before")
            if after and is_word_character(after):
                sides.append("after")
            if sides:
                failures.append(
                    f"{path}:{line_number}: add whitespace {' and '.join(sides)} **strong** markup"
                )

    if fence_character is not None:
        failures.append(f"{path}:{fence_line}: unclosed fenced code block")
    return failures


class VisibleTextParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in SKIP_HTML_TAGS:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in SKIP_HTML_TAGS and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.text.append(data)


def scan_rendered(path: pathlib.Path, public: pathlib.Path) -> list[str]:
    parser = VisibleTextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()

    failures: list[str] = []
    seen: set[tuple[str, str]] = set()
    for text in parser.text:
        for label, pattern in RENDERED_MARKERS.items():
            for match in pattern.finditer(text):
                context = re.sub(
                    r"\s+", " ", text[max(0, match.start() - 36) : match.end() + 36]
                ).strip()
                key = label, context
                if key in seen:
                    continue
                seen.add(key)
                relative = path.relative_to(public)
                failures.append(
                    f"{relative}: visible HTML contains unrendered {label} near {context!r}"
                )
    return failures


def main() -> int:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("content", nargs="?", default="content", type=pathlib.Path)
    argument_parser.add_argument("public", nargs="?", default="public", type=pathlib.Path)
    args = argument_parser.parse_args()
    content = args.content.resolve()
    public = args.public.resolve()
    if not content.is_dir():
        argument_parser.error(f"content directory does not exist: {content}")
    if not public.is_dir():
        argument_parser.error(f"rendered site directory does not exist: {public}")

    source_files = sorted(content.rglob("*.md"))
    html_files = sorted(public.rglob("*.html"))
    failures: list[str] = []
    for path in source_files:
        failures.extend(scan_source(path))
    for path in html_files:
        failures.extend(scan_rendered(path, public))

    if failures:
        print(f"markdown check failed: {len(failures)} issues", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(
        "markdown check passed: "
        f"{len(source_files)} source documents and {len(html_files)} rendered HTML files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
