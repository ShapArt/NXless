from __future__ import annotations

import copy
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .record import _git, sha256_file

def _run_gate(command: list[str], env: dict[str, str] | None = None) -> tuple[str, str]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    except OSError as exc:
        return "fail", str(exc)
    output = (proc.stdout + proc.stderr).strip()
    return ("pass" if proc.returncode == 0 else "fail", output)


def preflight(
    repo_root: Path,
    *,
    git_fn: Callable[..., str] = _git,
    run_gate: Callable[..., tuple[str, str]] = _run_gate,
) -> dict[str, Any]:
    devkitpro = os.environ.get("DEVKITPRO", "")
    atmosphere_root = os.environ.get("NXLESS_ATMOSPHERE_ROOT", "")
    blockers: list[str] = []

    toolchain_gate = "blocked"
    toolchain_output = ""
    if devkitpro:
        toolchain_gate, toolchain_output = run_gate(
            [str(repo_root / "scripts" / "verify-switch-toolchain.sh")], env=os.environ.copy()
        )
        if toolchain_gate != "pass":
            blockers.append("Switch toolchain gate failed")
    else:
        blockers.append("DEVKITPRO is not set")

    atmosphere_gate = "blocked"
    atmosphere_output = ""
    if atmosphere_root:
        atmosphere_gate, atmosphere_output = run_gate(
            [str(repo_root / "scripts" / "verify-atmosphere-source.sh"), atmosphere_root],
            env=os.environ.copy(),
        )
        if atmosphere_gate != "pass":
            blockers.append("Atmosphere source gate failed")
    else:
        blockers.append("NXLESS_ATMOSPHERE_ROOT is not set")

    info = {
        "git_commit": git_fn(repo_root, "rev-parse", "HEAD"),
        "git_clean": git_fn(repo_root, "status", "--porcelain") == "",
        "python": shutil.which("python3") or "",
        "cmake": shutil.which("cmake") or "",
        "devkitpro": devkitpro,
        "nxless_atmosphere_root": atmosphere_root,
        "docker": shutil.which("docker") or shutil.which("podman") or "",
        "toolchain_gate": toolchain_gate,
        "toolchain_output": toolchain_output,
        "atmosphere_gate": atmosphere_gate,
        "atmosphere_output": atmosphere_output,
        "blockers": blockers,
        "ready": not blockers,
    }
    return info


def _canonical_host_state(status: str, output: str) -> tuple[str, str]:
    if status == "pass":
        return "pass", ""
    lower = output.lower()
    network_markers = (
        "could not resolve host",
        "failed to resolve",
        "temporary failure in name resolution",
        "network is unreachable",
        "connection timed out",
    )
    if "github.com" in lower and any(marker in lower for marker in network_markers):
        return "blocked", output[-2000:]
    return "fail", output[-2000:]
