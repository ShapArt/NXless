#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
import sys

# Maintained local denylist. Online verification is recorded separately in release/PR evidence.
DENYLIST = {
    "010000000000000D": "Atmosphere creport",
    "010000000000000E": "Atmosphere fatal",
    "0100000000000019": "Atmosphere dmnt",
    "010000000000002B": "Atmosphere erpt",
    "0100000000000032": "Atmosphere ro",
    "0100000000000036": "Atmosphere spl",
}
TITLE_RE = re.compile(r"^01[0-9A-Fa-f]{14}$")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("title_id", nargs="?", default="0100000000004E58")
    args = parser.parse_args()
    title_id = args.title_id.upper()
    if not TITLE_RE.fullmatch(title_id):
        print("invalid title id format", file=sys.stderr)
        return 2
    if title_id in DENYLIST:
        print(f"collision: {title_id} ({DENYLIST[title_id]})", file=sys.stderr)
        return 1
    print(f"local collision check: PASS {title_id}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
