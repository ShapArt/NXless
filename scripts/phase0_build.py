#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ATMOSPHERE_COMMIT = "5388824"
ATMOSPHERE_TAG = "1.11.2"
ATMOSPHERE_URL = "https://github.com/Atmosphere-NX/Atmosphere.git"


class BuildError(RuntimeError):
    pass


def _git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _run_checked(command: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None) -> None:
    try:
        proc = subprocess.run(command, env=env, cwd=cwd, text=True, check=False)
    except OSError as exc:
        raise BuildError(f"could not run {command[0]}: {exc}") from exc
    if proc.returncode != 0:
        raise BuildError(f"command failed ({proc.returncode}): {' '.join(command)}")


def default_atmosphere_root(repo: Path) -> Path:
    return repo / "third_party" / "Atmosphere"


def default_record_path(repo: Path, commit: str) -> Path:
    return repo / "evidence" / f"phase0-hardware-{commit[:12]}.json"


def require_clean_commit(repo: Path) -> str:
    commit = _git(repo, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise BuildError("repository HEAD is not a full git commit")
    if _git(repo, "status", "--porcelain"):
        raise BuildError("source tree is dirty; commit or discard changes before the Phase 0 build")
    return commit


def require_new_record_path(record: Path) -> None:
    if record.exists():
        raise BuildError(f"evidence record already exists: {record}")


def ensure_atmosphere_checkout(
    repo: Path, atmosphere_root: Path, *, fetch_missing: bool
) -> None:
    git_dir = atmosphere_root / ".git"
    if not git_dir.exists():
        if atmosphere_root.exists() and any(atmosphere_root.iterdir()):
            raise BuildError(f"Atmosphere path exists but is not a git checkout: {atmosphere_root}")
        if not fetch_missing:
            raise BuildError(f"missing pinned Atmosphere checkout: {atmosphere_root}")
        atmosphere_root.parent.mkdir(parents=True, exist_ok=True)
        _run_checked(["git", "init", str(atmosphere_root)])
        _run_checked(["git", "-C", str(atmosphere_root), "remote", "add", "origin", ATMOSPHERE_URL])
        _run_checked(
            ["git", "-C", str(atmosphere_root), "fetch", "--depth", "1", "origin", "tag", ATMOSPHERE_TAG]
        )
        _run_checked(["git", "-C", str(atmosphere_root), "checkout", "--detach", "FETCH_HEAD"])

    _run_checked([str(repo / "scripts" / "verify-atmosphere-source.sh"), str(atmosphere_root)])


def run_pipeline(
    repo: Path,
    atmosphere_root: Path,
    record: Path,
    *,
    builder: str,
    fetch_atmosphere: bool,
) -> Path:
    require_clean_commit(repo)
    require_new_record_path(record)
    ensure_atmosphere_checkout(repo, atmosphere_root, fetch_missing=fetch_atmosphere)

    env = os.environ.copy()
    env["NXLESS_ATMOSPHERE_ROOT"] = str(atmosphere_root)

    _run_checked(["make", "-C", str(repo), "hardware-tool-test"], env=env)
    _run_checked(
        [
            "python3",
            str(repo / "scripts" / "phase0_hardware.py"),
            "new-record",
            "--repo",
            str(repo),
            "--output",
            str(record),
        ],
        env=env,
    )
    _run_checked(
        [
            "python3",
            str(repo / "scripts" / "phase0_hardware.py"),
            "record-host",
            "--repo",
            str(repo),
            "--record",
            str(record),
        ],
        env=env,
    )
    _run_checked(
        [
            "python3",
            str(repo / "scripts" / "phase0_hardware.py"),
            "record-build",
            "--repo",
            str(repo),
            "--record",
            str(record),
            "--builder",
            builder,
        ],
        env=env,
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the pinned one-command NXless Phase 0 verification and Switch package build"
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--atmosphere-root", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--builder", default=os.environ.get("USER", ""))
    parser.add_argument(
        "--no-fetch-atmosphere",
        action="store_true",
        help="require an existing pinned Atmosphere checkout instead of fetching it from GitHub",
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    try:
        commit = require_clean_commit(repo)
        atmosphere_root = (
            args.atmosphere_root.resolve() if args.atmosphere_root else default_atmosphere_root(repo)
        )
        record = args.record.resolve() if args.record else default_record_path(repo, commit)
        run_pipeline(
            repo,
            atmosphere_root,
            record,
            builder=args.builder,
            fetch_atmosphere=not args.no_fetch_atmosphere,
        )
        package = repo / "output" / "NXless-phase0.zip"
        data = json.loads(record.read_text(encoding="utf-8"))
        package_sha = data.get("build", {}).get("package_sha256", "")
        print(f"Phase 0 package: {package}")
        print(f"Evidence record: {record}")
        if package_sha:
            print(f"SHA-256: {package_sha}")
        return 0
    except (BuildError, OSError, json.JSONDecodeError) as exc:
        print(f"phase0 build failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
