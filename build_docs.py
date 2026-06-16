#!/usr/bin/env python3
"""Build docs/notebook.html and externalize large Vega-Lite specs.

Run from the repo root:

    python3 build_docs.py

Equivalent to:

    1. jupyter nbconvert --to html --execute main.ipynb --no-input \\
         --output notebook.html --output-dir docs/ \\
         --ExecutePreprocessor.timeout=240
    2. Walks the resulting HTML, finds every (function(spec, embedOpt){...})(SPEC, OPT)
       Vega-Lite IIFE, and for each spec larger than 50 KB, writes it to
       docs/charts/spec_<hash>.json and replaces the inline spec with the
       URL string. vega-embed handles URL strings natively, so the page
       still renders the same charts — they're just fetched lazily.
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
HTML = DOCS / "notebook.html"
THRESHOLD = 50_000  # only externalize specs bigger than this many chars


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


def externalize_specs() -> None:
    if CHARTS.exists():
        shutil.rmtree(CHARTS)
    CHARTS.mkdir(parents=True)

    html = HTML.read_text()
    out: list[str] = []
    cursor = 0
    count = 0
    saved = 0

    for m in re.finditer(r"\}\)\(\s*", html):
        invoke_end = m.end()
        parsed = find_balanced_json(html, invoke_end)
        if parsed is None:
            continue
        spec_end, spec_str = parsed
        if len(spec_str) < THRESHOLD:
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
    new = "".join(out)
    HTML.write_text(new)
    pct = 100 * (len(html) - len(new)) / len(html) if html else 0
    print(
        f"Externalized {count} specs ({saved:,} chars saved); "
        f"HTML {len(html):,} -> {len(new):,} chars ({pct:.0f}% smaller)"
    )


if __name__ == "__main__":
    print("Running nbconvert...")
    run_nbconvert()
    print("Externalizing large Vega-Lite specs...")
    externalize_specs()
    print("Done.")
