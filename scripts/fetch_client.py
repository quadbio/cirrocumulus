#!/usr/bin/env python3
"""Populate ``build/`` with the prebuilt web client from a published cirrocumulus wheel.

``cirrocumulus/client`` is a symlink to ``../build/``, which normally comes from
``yarn build``. That needs a node toolchain and ~50 npm packages via ``react-scripts``,
which is unmaintained -- not worth it for a fork that only changes Python. The published
wheels already ship the built client, so we unpack it from there instead.

Re-run after cloning, after deleting ``build/``, or to move to a newer client:

    python scripts/fetch_client.py [--version 1.1.61] [--force]

Only do this while the fork's changes stay server-side. If you ever patch ``src/``, the
client has to be built for real.
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path


DEFAULT_VERSION = "1.1.61"
ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
STAMP = BUILD / "CLIENT_VERSION"


def wheel_url(version: str) -> str:
    """Find the wheel for ``version`` on PyPI."""
    with urllib.request.urlopen(f"https://pypi.org/pypi/cirrocumulus/{version}/json") as response:
        meta = json.load(response)
    for entry in meta["urls"]:
        if entry["packagetype"] == "bdist_wheel":
            return entry["url"]
    raise SystemExit(f"no wheel published for cirrocumulus {version}")


def main() -> int:
    """Download and unpack the client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION, help="cirrocumulus release to take the client from")
    parser.add_argument("--force", action="store_true", help="re-fetch even if build/ is already populated")
    args = parser.parse_args()

    if STAMP.exists() and not args.force:
        current = STAMP.read_text().strip()
        if current == args.version:
            print(f"build/ already holds the {current} client; use --force to re-fetch")
            return 0
        print(f"build/ holds {current}, replacing with {args.version}")

    print(f"fetching cirrocumulus {args.version} wheel from PyPI")
    with urllib.request.urlopen(wheel_url(args.version)) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))

    members = [n for n in archive.namelist() if n.startswith("cirrocumulus/client/") and not n.endswith("/")]
    if not members:
        raise SystemExit(f"the cirrocumulus {args.version} wheel ships no client/ directory")

    if BUILD.exists():
        shutil.rmtree(BUILD)
    for name in members:
        target = BUILD / Path(name).relative_to("cirrocumulus/client")
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(name) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)

    STAMP.write_text(args.version + "\n")
    if not (BUILD / "index.html").exists():
        raise SystemExit("unpacked, but build/index.html is missing -- wheel layout changed")
    print(f"wrote {len(members)} files to {BUILD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
