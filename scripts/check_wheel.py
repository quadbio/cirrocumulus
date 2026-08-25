#!/usr/bin/env python3
"""Fail unless a built wheel actually ships the web client.

``cirrocumulus/client`` is a symlink to gitignored ``build/``. Hatchling follows it, so a
wheel built after ``yarn build`` carries the client -- but a wheel built with ``build/``
empty is produced *silently*, with no error and no client, and the failure only shows up
as a 404 on ``/`` at runtime. This is the gate that catches that.

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
