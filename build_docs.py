#!/usr/bin/env python3
"""Build docs/notebook.html and externalize heavy inline blocks.

Run from the repo root:

    python3 build_docs.py

What it does:

    1. jupyter nbconvert --to html --execute main.ipynb --no-input \\
         --output notebook.html --output-dir docs/ \\
         --ExecutePreprocessor.timeout=240
    2. Walks the resulting HTML and:
         - moves each large <style> block into docs/assets/style_<hash>.css
           and replaces it with a <link rel="stylesheet"> tag
         - moves each Vega-Lite IIFE spec into docs/charts/spec_<hash>.json
           and replaces it with the URL string (vega-embed fetches it)
       The browser caches each file separately, and the page renders the
       same charts/styling — it just doesn't ship all of it inline.
    3. Collapses runs of blank lines so the file is also readable.
"""
from __future__ import annotations
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
CHARTS = DOCS / "charts"
ASSETS = DOCS / "assets"
HTML = DOCS / "notebook.html"

SPEC_THRESHOLD = 50_000   # min spec size (chars) to externalize
STYLE_THRESHOLD = 10_000  # min style block size to externalize


def run_nbconvert() -> None:
    cmd = [
        sys.executable, "-m", "nbconvert", "--to", "html",
        "--execute", "main.ipynb",
        "--output", "notebook.html",
        "--output-dir", str(DOCS),
        "--no-input",
        "--ExecutePreprocessor.timeout=240",
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)


def find_balanced_json(text: str, start: int) -> tuple[int, str] | None:
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1, text[start:i + 1]
    return None


def externalize_styles(html: str) -> tuple[str, int, int]:
    """Move large <style>...</style> blocks to docs/assets/*.css."""
    saved = 0
    count = 0
    out: list[str] = []
    cursor = 0
    for m in re.finditer(r"<style(?:\s[^>]*)?>(.*?)</style>", html, re.DOTALL):
        body = m.group(1)
        if len(body) < STYLE_THRESHOLD:
            continue
        h = hashlib.md5(body.encode()).hexdigest()[:10]
        fname = f"style_{h}.css"
        (ASSETS / fname).write_text(body)
        link = f'<link rel="stylesheet" href="assets/{fname}">'
        out.append(html[cursor:m.start()])
        out.append(link)
        cursor = m.end()
        saved += (m.end() - m.start()) - len(link)
        count += 1
    out.append(html[cursor:])
    return "".join(out), count, saved


def externalize_specs(html: str) -> tuple[str, int, int]:
    """Move big Vega-Lite specs to docs/charts/*.json."""
    saved = 0
    count = 0
    out: list[str] = []
    cursor = 0
    for m in re.finditer(r"\}\)\(\s*", html):
        invoke_end = m.end()
        parsed = find_balanced_json(html, invoke_end)
        if parsed is None:
            continue
        spec_end, spec_str = parsed
        if len(spec_str) < SPEC_THRESHOLD:
            continue
        rest = html[spec_end:spec_end + 4].lstrip()
        if not rest.startswith(","):
            continue
        h = hashlib.md5(spec_str.encode()).hexdigest()[:10]
        fname = f"spec_{h}.json"
        (CHARTS / fname).write_text(spec_str)
        replacement = f'"charts/{fname}"'
        out.append(html[cursor:invoke_end])
        out.append(replacement)
        cursor = spec_end
        count += 1
        saved += len(spec_str) - len(replacement)
    out.append(html[cursor:])
    return "".join(out), count, saved


def collapse_blank_lines(html: str) -> str:
    """Collapse runs of 2+ blank lines to a single blank line."""
    return re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", html)


def main() -> None:
    print("Running nbconvert...")
    run_nbconvert()

    if CHARTS.exists():
        shutil.rmtree(CHARTS)
    CHARTS.mkdir(parents=True)
    if ASSETS.exists():
        shutil.rmtree(ASSETS)
    ASSETS.mkdir(parents=True)

    html = HTML.read_text()
    orig_size, orig_lines = len(html), html.count("\n") + 1

    html, n_styles, saved_styles = externalize_styles(html)
    html, n_specs, saved_specs = externalize_specs(html)
    html = collapse_blank_lines(html)

    HTML.write_text(html)
    new_size, new_lines = len(html), html.count("\n") + 1
    print(
        f"Moved {n_styles} style blocks ({saved_styles:,} chars) -> docs/assets/\n"
        f"Moved {n_specs} chart specs ({saved_specs:,} chars) -> docs/charts/\n"
        f"HTML:  {orig_size:,} -> {new_size:,} chars  "
        f"({100*(orig_size-new_size)/orig_size:.0f}% smaller)\n"
        f"Lines: {orig_lines:,} -> {new_lines:,}  "
        f"({100*(orig_lines-new_lines)/orig_lines:.0f}% fewer)"
    )


if __name__ == "__main__":
    main()
