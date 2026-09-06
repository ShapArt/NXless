#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from phase0_hw.echo import EchoServer
from phase0_hw.gates import (
    _canonical_host_state,
    _run_gate,
    collect_host_verification as _collect_host_verification_impl,
    preflight as _preflight_impl,
    record_switch_build as _record_switch_build_impl,
    record_probe_build as _record_probe_build_impl,
)
from phase0_hw.record import (
    ATMOSPHERE_COMMIT,
    ATMOSPHERE_VERSION,
    DEVKITA64,
    HOS,
    LIBNX_COMMIT,
    LIBNX_VERSION,
    PROGRAM_ID,
    REQUIRED_COUNTS,
    _git,
    add_lifecycle_attempt,
    append_boot,
    new_record,
    render_markdown,
    sha256_file,
    synthetic_complete_record,
    validate_record,
)


def preflight(repo_root: Path) -> dict[str, Any]:
    return _preflight_impl(repo_root, git_fn=_git, run_gate=_run_gate)


def collect_host_verification(record: dict[str, Any], repo_root: Path):
    return _collect_host_verification_impl(record, repo_root, run_gate=_run_gate)


def record_switch_build(record: dict[str, Any], repo_root: Path, *, builder: str = ""):
    return _record_switch_build_impl(
        record,
        repo_root,
        builder=builder,
        git_fn=_git,
        preflight_fn=preflight,
        run_gate=_run_gate,
    )


def record_probe_build(record: dict[str, Any], repo_root: Path):
    return _record_probe_build_impl(
        record,
        repo_root,
        git_fn=_git,
        run_gate=_run_gate,
    )


def main() -> int:
    from phase0_hw.cli import main as cli_main
    return cli_main(
        collect_host_verification=collect_host_verification,
        record_switch_build=record_switch_build,
        record_probe_build=record_probe_build,
        preflight=preflight,
    )


if __name__ == "__main__":
    raise SystemExit(main())
