#!/usr/bin/env python3
"""Generate the homepage hero architecture diagram.

The OINK landing hero paints its media as two CSS background images -- one per
colour scheme -- so a diagram needs a separate file per theme, and a bilingual
site needs one pair per language. Four hand-maintained SVGs would drift, so the
geometry and the copy live here and the files are generated:

    static/img/architecture-{light,dark}.svg
    static/img/architecture-zh-{light,dark}.svg

Facts drawn from the pg_exporter source tree (exporter/arg.go, main.go,
composite.go, patroni.go, pgbackrest.go): PostgreSQL over libpq, PgBouncer
through its admin console, Patroni through its own Prometheus endpoint,
pgBackRest by executing the local CLI, all merged and served on :9630/metrics.

Run from the site root:

    python3 bin/build_architecture_diagram.py
"""

from __future__ import annotations

import pathlib
import sys


# --------------------------------------------------------------------------
# Canvas geometry. One coordinate system, shared by all four files.
# --------------------------------------------------------------------------

# The drawing is laid out in a 0..640 x 0..452 box; the viewBox adds a margin
# so card shadows and the caption row are not clipped at the edges.
WIDTH = 640
HEIGHT = 480
VIEW_X, VIEW_Y, VIEW_W, VIEW_H = -12, -10, 664, 486

SRC_X, SRC_W, SRC_H = 0, 150, 76
SRC_YS = (36, 132, 228, 324)

CORE_X, CORE_W, CORE_Y, CORE_H = 232, 176, 92, 252
CORE_CX = CORE_X + CORE_W / 2          # 320
CORE_CY = CORE_Y + CORE_H / 2          # 218

SINK_X, SINK_W, SINK_H = 490, 150, 92
SINK_YS = (108, 236)

CONF_X, CONF_W, CONF_Y, CONF_H = 232, 176, 398, 54

# Where each source connector lands on the core's left edge.
CORE_ENTRY_YS = (140, 195, 250, 300)

FONT_SANS = (
    "-apple-system,BlinkMacSystemFont,&#39;Segoe UI&#39;,Roboto,"
    "&#39;Helvetica Neue&#39;,Arial,&#39;PingFang SC&#39;,"
    "&#39;Hiragino Sans GB&#39;,&#39;Microsoft YaHei&#39;,"
    "&#39;Noto Sans SC&#39;,sans-serif"
)
FONT_MONO = (
    "&#39;SFMono-Regular&#39;,&#39;Cascadia Code&#39;,&#39;Roboto Mono&#39;,"
    "Menlo,Consolas,monospace"
)


# --------------------------------------------------------------------------
# Palettes. Values mirror OINK's own light and dark brand tokens so the
# diagram sits on the hero as if the theme had drawn it.
# --------------------------------------------------------------------------

LIGHT = {
    "surface": "#ffffff",
    "surface_alt": "#f6f9fc",
    "line": "rgba(48,74,105,0.16)",
    "line_soft": "rgba(48,74,105,0.10)",
    "wire": "rgba(48,74,105,0.34)",
    "ink": "#16222e",
    "sub": "#586b80",
    "muted": "#8494a6",
    "chip": "rgba(48,74,105,0.05)",
    "core_fill": "#ffffff",
    "core_tint": "rgba(36,95,148,0.05)",
    "shadow": "rgba(23,42,66,0.13)",
    "shadow_core": "rgba(23,42,66,0.20)",
    "on_accent": "#ffffff",
    "accent": {
        "postgres": "#245f94",
        "bouncer": "#2f7d6d",
        "patroni": "#7a5aa8",
        "backrest": "#b4762e",
        "core": "#1d588c",
        "prometheus": "#d95f2b",
        "victoria": "#cf4436",
        "config": "#5d7189",
    },
}

DARK = {
    "surface": "#121c29",
    "surface_alt": "#182435",
    "line": "rgba(148,176,210,0.20)",
    "line_soft": "rgba(148,176,210,0.12)",
    "wire": "rgba(148,176,210,0.34)",
    "ink": "#e8eef6",
    "sub": "#9aa9bd",
    "muted": "#6f7f94",
    "chip": "rgba(148,176,210,0.09)",
    "core_fill": "#16233340",
    "core_tint": "rgba(127,184,232,0.07)",
    "shadow": "rgba(2,8,18,0.55)",
    "shadow_core": "rgba(2,8,18,0.70)",
    "on_accent": "#0b1119",
    "accent": {
        "postgres": "#5da2dd",
        "bouncer": "#4fb3a0",
        "patroni": "#a992d8",
        "backrest": "#e0a35c",
        "core": "#7fb8e8",
        "prometheus": "#f2884f",
        "victoria": "#ef6a5c",
        "config": "#93a3b8",
    },
}


# --------------------------------------------------------------------------
# Copy. Only these strings differ between the two languages.
# --------------------------------------------------------------------------

EN = {
    "alt": (
        "PG Exporter architecture: PostgreSQL, PgBouncer, Patroni, and "
        "pgBackRest are collected by one PG Exporter process, which serves "
        "merged metrics on :9630/metrics for Prometheus and VictoriaMetrics."
    ),
    "cap_left": "TARGETS",
    "cap_core": "EXPORTER",
    "cap_right": "SCRAPED BY",
    "sources": (
        ("PostgreSQL", "SQL · libpq"),
        ("PgBouncer", "SHOW · admin"),
        ("Patroni", "HTTP · REST"),
        ("pgBackRest", "CLI · JSON"),
    ),
    "core_title": "PG Exporter",
    "core_chips": (
        "collectors · YAML + SQL",
        "planner · version + role",
        "cache · TTL + timeout",
    ),
    "core_endpoint": ":9630 · /metrics",
    "core_note": "/explain · /stat · /reload",
    "sinks": (
        ("Prometheus", "pull · scrape_interval"),
        ("VictoriaMetrics", "PromQL / MetricsQL"),
    ),
    "scrape": "scrape",
    "config_title": "pg_exporter.yml",
    "config_sub": "58 files · 600+ metrics",
    "config_note": "declarative",
}

ZH = {
    "alt": (
        "PG Exporter 架构图：PostgreSQL、PgBouncer、Patroni 与 pgBackRest 由同一个 "
        "PG Exporter 进程采集，合并后通过 :9630/metrics 供 Prometheus 与 "
        "VictoriaMetrics 抓取。"
    ),
    "cap_left": "监控对象",
    "cap_core": "导出器",
    "cap_right": "抓取方",
    "sources": (
        ("PostgreSQL", "SQL · libpq"),
        ("PgBouncer", "SHOW · 管理台"),
        ("Patroni", "HTTP · REST"),
        ("pgBackRest", "CLI · JSON"),
    ),
    "core_title": "PG Exporter",
    "core_chips": (
        "采集器 · YAML + SQL",
        "规划器 · 版本 + 角色",
        "缓存 · TTL + 超时",
    ),
    "core_endpoint": ":9630 · /metrics",
    "core_note": "/explain · /stat · /reload",
    "sinks": (
        ("Prometheus", "拉取 · 定期抓取"),
        ("VictoriaMetrics", "PromQL / MetricsQL"),
    ),
    "scrape": "抓取",
    "config_title": "pg_exporter.yml",
    "config_sub": "58 个文件 · 600+ 指标",
    "config_note": "声明式",
}


# --------------------------------------------------------------------------
# Glyphs. Each path is drawn inside a 20x20 box and stroked in its accent
# colour; the tile scales and centres it.
# --------------------------------------------------------------------------

GLYPHS = {
    # A database cylinder.
    "postgres": [
        ("path", "M3 4.6C3 3 6.1 1.8 10 1.8s7 1.2 7 2.8-3.1 2.8-7 2.8-7-1.2-7-2.8Z"),
        ("path", "M3 4.6v10.8c0 1.6 3.1 2.8 7 2.8s7-1.2 7-2.8V4.6"),
        ("path", "M3 10c0 1.6 3.1 2.8 7 2.8s7-1.2 7-2.8"),
    ],
    # Three client lanes pooled into one connection.
    "bouncer": [
        ("path", "M2.2 4.4h5"),
        ("path", "M2.2 10h5"),
        ("path", "M2.2 15.6h5"),
        ("path", "M7.2 4.4 12.2 10"),
        ("path", "M7.2 10h5"),
        ("path", "M7.2 15.6 12.2 10"),
        ("circle", "14.8 10 2.5"),
    ],
    # A leader with two followers.
    "patroni": [
        ("path", "M10 6.6 4.4 13.6"),
        ("path", "M10 6.6l5.6 7"),
        ("circle", "10 4.4 2.6"),
        ("circle", "3.6 15.6 2.3"),
        ("circle", "16.4 15.6 2.3"),
    ],
    # An archive box.
    "backrest": [
        ("path", "M2.2 3.4h15.6v3.8H2.2z"),
        ("path", "M3.6 7.2v8.4c0 1.1.9 2 2 2h8.8c1.1 0 2-.9 2-2V7.2"),
        ("path", "M8 11h4"),
    ],
    # Export: a frame with an arrow leaving it.
    "core": [
        ("path", "M15.4 11.6v3.8c0 1.2-1 2.2-2.2 2.2H4.8c-1.2 0-2.2-1-2.2-2.2V6.8c0-1.2 1-2.2 2.2-2.2h3.8"),
        ("path", "M11.6 2.4h6v6"),
        ("path", "M9.4 10.6 17.6 2.4"),
    ],
    # Prometheus: the capped flame.
    "prometheus": [
        ("path", "M10 2.2c3 3.2 4.8 5.8 4.8 9a4.8 4.8 0 0 1-9.6 0c0-2.6 1.4-4.6 3.2-6.2 0 2 .6 3.4 1.6 4.4.6-2.2.6-4.8 0-7.2Z"),
        ("path", "M6 17.4h8"),
    ],
    # VictoriaMetrics: the chevron.
    "victoria": [
        ("path", "M3.2 3.4 10 17 16.8 3.4", "2.4"),
    ],
    # A configuration document.
    "config": [
        ("path", "M4 2.6h7.4l4.6 4.6v10.2c0 .6-.5 1-1 1H4c-.6 0-1-.4-1-1V3.6c0-.6.4-1 1-1Z"),
        ("path", "M11.4 2.6v4.6H16"),
        ("path", "M5.8 11h7.2"),
        ("path", "M5.8 14.2h5"),
    ],
}


def glyph(kind: str, x: float, y: float, size: float, colour: str) -> str:
    """Render one 20x20 glyph scaled into a `size` box at (x, y)."""

    scale = size / 20.0
    parts = [
        f'<g transform="translate({x:g} {y:g}) scale({scale:g})" fill="none" '
        f'stroke="{colour}" stroke-width="1.7" stroke-linecap="round" '
        f'stroke-linejoin="round">'
    ]
    for entry in GLYPHS[kind]:
        shape, spec = entry[0], entry[1]
        weight = f' stroke-width="{entry[2]}"' if len(entry) > 2 else ""
        if shape == "path":
            parts.append(f'<path d="{spec}"{weight}/>')
        else:
            cx, cy, r = spec.split()
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"{weight}/>')
    parts.append("</g>")
    return "".join(parts)


def tile(kind: str, cx: float, cy: float, box: float, colour: str) -> str:
    """A rounded, tinted plate with the glyph centred inside it."""

    x, y = cx - box / 2, cy - box / 2
    pad = box * 0.24
    return (
        f'<rect x="{x:g}" y="{y:g}" width="{box:g}" height="{box:g}" '
        f'rx="{box * 0.3:g}" fill="{colour}" fill-opacity="0.12"/>'
        + glyph(kind, x + pad, y + pad, box - 2 * pad, colour)
    )


def text(
    content: str,
    x: float,
    y: float,
    size: float,
    fill: str,
    *,
    weight: int = 400,
    anchor: str = "start",
    mono: bool = False,
    spacing: float | None = None,
) -> str:
    attrs = [
        f'x="{x:g}"',
        f'y="{y:g}"',
        f'font-family="{FONT_MONO if mono else FONT_SANS}"',
        f'font-size="{size:g}"',
        f'font-weight="{weight}"',
        f'fill="{fill}"',
    ]
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if spacing is not None:
        attrs.append(f'letter-spacing="{spacing:g}"')
    return f'<text {" ".join(attrs)}>{escape(content)}</text>'


def escape(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def card(
    x: float,
    y: float,
    w: float,
    h: float,
    palette: dict,
    *,
    radius: float = 13,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: float = 1,
    shadow: str = "card-shadow",
) -> str:
    return (
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
        f'rx="{radius:g}" fill="{fill or palette["surface"]}" '
        f'stroke="{stroke or palette["line"]}" stroke-width="{stroke_width:g}" '
        f'filter="url(#{shadow})"/>'
    )


# --------------------------------------------------------------------------
# Diagram
# --------------------------------------------------------------------------


def build(copy: dict, palette: dict, theme: str) -> str:
    accent = palette["accent"]
    out: list[str] = []
    add = out.append

    add(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{VIEW_X} {VIEW_Y} {VIEW_W} {VIEW_H}" '
        f'width="{VIEW_W}" height="{VIEW_H}" role="img" '
        f'aria-labelledby="diagram-title">'
    )
    add(f"<title id=\"diagram-title\">{escape(copy['alt'])}</title>")

    # ---- defs -------------------------------------------------------------
    add("<defs>")
    add(
        '<filter id="card-shadow" x="-25%" y="-40%" width="150%" height="190%">'
        f'<feDropShadow dx="0" dy="4" stdDeviation="7" '
        f'flood-color="{palette["shadow"]}"/></filter>'
    )
    add(
        '<filter id="core-shadow" x="-30%" y="-20%" width="160%" height="150%">'
        f'<feDropShadow dx="0" dy="10" stdDeviation="16" '
        f'flood-color="{palette["shadow_core"]}"/></filter>'
    )
    add(
        f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0 1.2 9 5 0 8.8 2 5Z" fill="{palette["wire"]}"/></marker>'
    )
    add(
        f'<marker id="arrow-out" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0 1.2 9 5 0 8.8 2 5Z" fill="{accent["core"]}"/></marker>'
    )
    add(
        '<linearGradient id="core-face" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{accent["core"]}" stop-opacity="0.10"/>'
        f'<stop offset="0.55" stop-color="{accent["core"]}" stop-opacity="0.02"/>'
        f'<stop offset="1" stop-color="{accent["core"]}" stop-opacity="0.06"/>'
        "</linearGradient>"
    )
    add("</defs>")

    # Dash motion reads as data in flight; a reduced-motion reader gets the
    # same picture with the dashes at rest.
    add(
        "<style>"
        ".flow{stroke-dasharray:5 11;animation:flow 2.6s linear infinite}"
        ".flow--out{animation-duration:2s}"
        "@keyframes flow{to{stroke-dashoffset:-32}}"
        "@media (prefers-reduced-motion:reduce){.flow{animation:none}}"
        "</style>"
    )

    # ---- column captions --------------------------------------------------
    add(text(copy["cap_left"], SRC_X + 4, 16, 9.5, palette["muted"],
             weight=600, spacing=1.3))
    add(text(copy["cap_core"], CORE_CX, 16, 9.5, palette["muted"],
             weight=600, anchor="middle", spacing=1.3))
    add(text(copy["cap_right"], WIDTH - 4, 16, 9.5, palette["muted"],
             weight=600, anchor="end", spacing=1.3))

    # ---- connectors: sources into the core --------------------------------
    source_kinds = ("postgres", "bouncer", "patroni", "backrest")
    for index, (top, entry) in enumerate(zip(SRC_YS, CORE_ENTRY_YS)):
        cy = top + SRC_H / 2
        d = (
            f"M{SRC_X + SRC_W} {cy} C{SRC_X + SRC_W + 38} {cy} "
            f"{CORE_X - 38} {entry} {CORE_X} {entry}"
        )
        add(
            f'<path d="{d}" fill="none" stroke="{palette["wire"]}" '
            f'stroke-width="1.3" marker-end="url(#arrow)"/>'
        )
        add(
            f'<path class="flow" d="{d}" fill="none" '
            f'stroke="{accent[source_kinds[index]]}" stroke-width="1.9" '
            f'stroke-linecap="round" opacity="0.85" '
            f'style="animation-delay:-{index * 0.55:g}s"/>'
        )

    # ---- connectors: core out to the scrapers -----------------------------
    fork_x = CORE_X + CORE_W + 28
    add(
        f'<path d="M{CORE_X + CORE_W} {CORE_CY} H{fork_x}" fill="none" '
        f'stroke="{palette["wire"]}" stroke-width="1.3"/>'
    )
    add(
        f'<circle cx="{fork_x}" cy="{CORE_CY}" r="2.6" '
        f'fill="{accent["core"]}"/>'
    )
    for index, top in enumerate(SINK_YS):
        cy = top + SINK_H / 2
        d = (
            f"M{fork_x} {CORE_CY} C{fork_x + 22} {CORE_CY} "
            f"{SINK_X - 26} {cy} {SINK_X} {cy}"
        )
        add(
            f'<path d="{d}" fill="none" stroke="{palette["wire"]}" '
            f'stroke-width="1.3" marker-end="url(#arrow-out)"/>'
        )
        add(
            f'<path class="flow flow--out" d="{d}" fill="none" '
            f'stroke="{accent["core"]}" stroke-width="1.9" '
            f'stroke-linecap="round" opacity="0.8" '
            f'style="animation-delay:-{index * 0.4:g}s"/>'
        )
    add(text(copy["scrape"], fork_x + 28, CORE_CY + 3.5, 9,
             palette["muted"], anchor="middle"))

    # ---- connector: configuration into the core ---------------------------
    add(
        f'<path d="M{CORE_CX} {CONF_Y - 4} V{CORE_Y + CORE_H + 6}" '
        f'fill="none" stroke="{palette["wire"]}" stroke-width="1.3" '
        f'stroke-dasharray="4 4" marker-end="url(#arrow)"/>'
    )
    add(text(copy["config_note"], CORE_CX + 12, CONF_Y - 24, 9,
             palette["muted"]))

    # ---- source cards -----------------------------------------------------
    for kind, top, (title, sub) in zip(source_kinds, SRC_YS, copy["sources"]):
        add(card(SRC_X, top, SRC_W, SRC_H, palette))
        add(tile(kind, SRC_X + 27, top + SRC_H / 2, 30, accent[kind]))
        add(text(title, SRC_X + 48, top + 34, 12.5, palette["ink"], weight=600))
        add(text(sub, SRC_X + 48, top + 50, 9, palette["sub"]))

    # ---- core -------------------------------------------------------------
    add(
        f'<rect x="{CORE_X}" y="{CORE_Y}" width="{CORE_W}" height="{CORE_H}" '
        f'rx="16" fill="{palette["surface"]}" filter="url(#core-shadow)"/>'
    )
    add(
        f'<rect x="{CORE_X}" y="{CORE_Y}" width="{CORE_W}" height="{CORE_H}" '
        f'rx="16" fill="url(#core-face)" stroke="{accent["core"]}" '
        f'stroke-opacity="0.45" stroke-width="1.4"/>'
    )
    add(tile("core", CORE_CX, CORE_Y + 32, 36, accent["core"]))
    add(text(copy["core_title"], CORE_CX, CORE_Y + 68, 15.5, palette["ink"],
             weight=700, anchor="middle"))
    add(
        f'<path d="M{CORE_X + 20} {CORE_Y + 80} H{CORE_X + CORE_W - 20}" '
        f'stroke="{palette["line"]}" stroke-width="1"/>'
    )

    chip_x, chip_w, chip_h = CORE_X + 16, CORE_W - 32, 26
    for index, label in enumerate(copy["core_chips"]):
        chip_y = CORE_Y + 90 + index * 30
        add(
            f'<rect x="{chip_x}" y="{chip_y}" width="{chip_w}" '
            f'height="{chip_h}" rx="8" fill="{palette["chip"]}" '
            f'stroke="{palette["line_soft"]}" stroke-width="1"/>'
        )
        add(text(label, CORE_CX, chip_y + 16.5, 9.3, palette["sub"],
                 anchor="middle"))

    endpoint_y = CORE_Y + 188
    add(
        f'<rect x="{chip_x}" y="{endpoint_y}" width="{chip_w}" height="28" '
        f'rx="9" fill="{accent["core"]}"/>'
    )
    add(text(copy["core_endpoint"], CORE_CX, endpoint_y + 18.5, 10.5,
             palette["on_accent"], weight=700, anchor="middle", mono=True))
    add(text(copy["core_note"], CORE_CX, CORE_Y + 234, 8.8, palette["muted"],
             anchor="middle", mono=True))

    # ---- sink cards -------------------------------------------------------
    for kind, top, (title, sub) in zip(
        ("prometheus", "victoria"), SINK_YS, copy["sinks"]
    ):
        add(card(SINK_X, top, SINK_W, SINK_H, palette))
        add(tile(kind, SINK_X + SINK_W / 2, top + 30, 34, accent[kind]))
        add(text(title, SINK_X + SINK_W / 2, top + 66, 12.5, palette["ink"],
                 weight=600, anchor="middle"))
        add(text(sub, SINK_X + SINK_W / 2, top + 81, 9, palette["sub"],
                 anchor="middle"))

    # ---- configuration card ----------------------------------------------
    add(card(CONF_X, CONF_Y, CONF_W, CONF_H, palette, radius=12))
    add(tile("config", CONF_X + 27, CONF_Y + CONF_H / 2, 26, accent["config"]))
    add(text(copy["config_title"], CONF_X + 48, CONF_Y + 24, 11,
             palette["ink"], weight=600, mono=True))
    add(text(copy["config_sub"], CONF_X + 48, CONF_Y + 39, 8.8,
             palette["sub"]))

    add("</svg>")
    return "".join(out) + "\n"


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    target = root / "static" / "img"
    if not target.is_dir():
        print(f"missing output directory: {target}", file=sys.stderr)
        return 1

    variants = (
        ("architecture-light.svg", EN, LIGHT, "light"),
        ("architecture-dark.svg", EN, DARK, "dark"),
        ("architecture-zh-light.svg", ZH, LIGHT, "light"),
        ("architecture-zh-dark.svg", ZH, DARK, "dark"),
    )
    for name, copy, palette, theme in variants:
        path = target / name
        path.write_text(build(copy, palette, theme), encoding="utf-8")
        print(f"wrote {path.relative_to(root)} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
