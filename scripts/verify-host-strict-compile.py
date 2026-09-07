#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def production_sources(repo: Path) -> list[Path]:
    roots = (repo / "common" / "src", repo / "sysmodule" / "source")
    return sorted(path for root in roots for path in root.rglob("*.cpp"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Strict host compile of NXless production translation units")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    repo = args.repo.resolve()

    compiler = shutil.which("g++") or shutil.which("c++")
    if not compiler:
        print("strict production compile: BLOCKED (no host C++ compiler)", file=sys.stderr)
        return 2

    sources = production_sources(repo)
    if not sources:
        print("strict production compile: FAIL (no production sources found)", file=sys.stderr)
        return 3

    out_root = repo / "build" / "strict-production"
    out_root.mkdir(parents=True, exist_ok=True)
    base_flags = [
        compiler,
        "-std=c++20",
        "-Wall",
        "-Wextra",
        "-Wpedantic",
        "-Wconversion",
        "-Wsign-conversion",
        "-Werror",
        "-fno-exceptions",
        "-fno-rtti",
        f"-I{repo / 'common' / 'include'}",
        f"-I{repo / 'sysmodule' / 'include'}",
    ]

    for source in sources:
        rel = source.relative_to(repo)
        obj = out_root / rel.with_suffix(".o")
        obj.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [*base_flags, "-c", str(source), "-o", str(obj)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            print(f"strict production compile: FAIL ({rel})", file=sys.stderr)
            if proc.stdout:
                print(proc.stdout, file=sys.stderr, end="")
            if proc.stderr:
                print(proc.stderr, file=sys.stderr, end="")
            return proc.returncode or 1

    print(f"strict production compile: PASS ({len(sources)} translation units)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
