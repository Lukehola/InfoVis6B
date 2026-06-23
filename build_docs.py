#!/usr/bin/env python3
"""Rebuild the Jupyter Book site under docs/.

Run from the repo root:

    python3 build_docs.py

Pipeline:

    1. jupyter-book build .          -> writes _build/html
    2. rm -rf docs/ && cp -r _build/html docs
    3. touch docs/.nojekyll          -> GitHub Pages skips Jekyll, so the
                                        underscore-prefixed Sphinx asset
                                        dirs (_static, _images, etc.) are
                                        served as-is.

The site is then ready to commit and push:

    git add docs/ && git commit -m 'rebuild docs' && git push
"""
from __future__ import annotations
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "_build" / "html"
DOCS = ROOT / "docs"


def main() -> None:
    # Re-import each run so a fresh interpreter picks up new config files.
    from jupyter_book.cli.main import main as jb_main

    if (ROOT / "_build").exists():
        shutil.rmtree(ROOT / "_build")
    if DOCS.exists():
        shutil.rmtree(DOCS)

    print("Running jupyter-book build...")
    try:
        jb_main(["build", str(ROOT)])
    except SystemExit as e:
        if e.code not in (0, None):
            raise

    if not BUILD.exists():
        sys.exit(f"jupyter-book did not produce {BUILD}")

    print(f"Copying {BUILD} -> {DOCS}")
    shutil.copytree(BUILD, DOCS)
    (DOCS / ".nojekyll").touch()
    print("Done. Site is under docs/")


if __name__ == "__main__":
    main()
