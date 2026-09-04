from __future__ import annotations

import copy
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .gate_common import _run_gate, preflight
from .schema import _git, sha256_file

def record_switch_build(
    record: dict[str, Any],
    repo_root: Path,
    *,
    builder: str = "",
    git_fn: Callable[..., str] = _git,
    preflight_fn: Callable[..., dict[str, Any]] = preflight,
    run_gate: Callable[..., tuple[str, str]] = _run_gate,
) -> tuple[dict[str, Any], list[str]]:
    updated = copy.deepcopy(record)
    build = updated["build"]
    blockers: list[str] = []
    current_commit = git_fn(repo_root, "rev-parse", "HEAD")
    current_clean = git_fn(repo_root, "status", "--porcelain") == ""

    if not re.fullmatch(r"[0-9a-f]{40}", current_commit):
        blockers.append("current repository HEAD is not a full git commit")
        return updated, blockers
    if build.get("nxless_commit") != current_commit:
        blockers.append("record commit does not match current HEAD")
        return updated, blockers
    if not current_clean:
        blockers.append("source tree must be clean before Switch build")
        return updated, blockers
    if build.get("source_tree_clean") is not True:
        blockers.append("record was created from a dirty source tree")
        return updated, blockers

    pf = preflight_fn(repo_root)
    if not pf.get("ready"):
        blockers.extend(str(item) for item in pf.get("blockers", []))
        return updated, blockers
    if pf.get("toolchain_gate") != "pass":
        blockers.append("Switch toolchain gate is not PASS")
        return updated, blockers
    if pf.get("atmosphere_gate") != "pass":
        blockers.append("Atmosphere source gate is not PASS")
        return updated, blockers

    package = repo_root / "output" / "NXless-phase0.zip"
    try:
        package.unlink(missing_ok=True)
    except OSError as exc:
        blockers.append(f"could not remove stale package before clean build: {exc}")
        return updated, blockers

    env = os.environ.copy()
    clean_status, clean_output = run_gate(
        ["make", "-C", str(repo_root / "sysmodule"), "clean"], env=env
    )
    if clean_status != "pass":
        blockers.append("sysmodule clean failed: " + clean_output[-1000:])
        return updated, blockers

    build_status, build_output = run_gate(
        ["make", "-C", str(repo_root), "switch-package"], env=env
    )
    if build_status != "pass":
        blockers.append("clean Switch package build failed: " + build_output[-1000:])
        return updated, blockers
    if not package.is_file():
        blockers.append("clean Switch build did not produce output/NXless-phase0.zip")
        return updated, blockers

    build.update(
        {
            "nxless_commit": current_commit,
            "package_sha256": sha256_file(package),
            "build_date_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "builder": builder,
            "source_tree_clean": True,
            "switch_toolchain_verified": True,
            "atmosphere_source_verified": True,
            "clean_switch_build": True,
            "toolchain_gate_output": str(pf.get("toolchain_output", ""))[-2000:],
            "atmosphere_gate_output": str(pf.get("atmosphere_output", ""))[-2000:],
        }
    )
    return updated, blockers
