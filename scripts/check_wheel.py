#!/usr/bin/env python3
"""Fail unless a built wheel actually ships the web client.

An empty ``build/`` yields a client-less wheel silently -- no error, just a 404 on ``/``
at runtime. See FORK.md.

    python scripts/check_wheel.py dist/cirrocumulus-*.whl
"""

from __future__ import annotations

import fnmatch
import sys
import zipfile

INDEX = "cirrocumulus/client/index.html"
BUNDLE = "cirrocumulus/client/static/js/*.js"


def main(path: str) -> int:
    names = zipfile.ZipFile(path).namelist()
    bundles = fnmatch.filter(names, BUNDLE)
    if INDEX not in names or not bundles:
        sys.exit(
            f"{path} ships no web client "
            f"({INDEX}: {INDEX in names}, {BUNDLE}: {len(bundles)}).\n"
            "Populate build/ with `yarn build` and rebuild -- see FORK.md."
        )
    print(f"{path}: {len(names)} files, client entry point {bundles[0]}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <wheel>")
    sys.exit(main(sys.argv[1]))
