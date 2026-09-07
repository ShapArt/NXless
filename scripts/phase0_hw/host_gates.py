from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

from .gate_common import _run_gate, _canonical_host_state

def collect_host_verification(
    record: dict[str, Any],
    repo_root: Path,
    *,
    run_gate: Callable[..., tuple[str, str]] = _run_gate,
) -> tuple[dict[str, Any], list[str]]:
    updated = copy.deepcopy(record)
    hv = updated["host_verification"]
    blockers: list[str] = []

    canonical_status, canonical_output = run_gate(["make", "-C", str(repo_root), "host-test"])
    canonical_state, canonical_reason = _canonical_host_state(canonical_status, canonical_output)
    hv["canonical_host_test"] = canonical_state
    hv["canonical_block_reason"] = canonical_reason

    offline_status = "pass"
    if canonical_state != "pass":
        offline_status, _ = run_gate(["make", "-C", str(repo_root), "host-test-offline"])

    strict_status, _ = run_gate(
        ["python3", str(repo_root / "scripts" / "verify-host-strict-compile.py"), "--repo", str(repo_root)]
    )
    package_status, _ = run_gate(["make", "-C", str(repo_root), "verify-package-policy"])
    locks_status, _ = run_gate(["make", "-C", str(repo_root), "verify-locks"])
    title_status, _ = run_gate(["make", "-C", str(repo_root), "check-title-id"])
    diff_status, _ = run_gate(["git", "-C", str(repo_root), "diff", "--check"])

    hv["strict_compile"] = strict_status == "pass"
    hv["package_verifier"] = package_status == "pass"
    hv["dependency_lock_verifier"] = locks_status == "pass"
    hv["title_id_collision_gate"] = title_status == "pass"
    hv["git_diff_check"] = diff_status == "pass"

    sanitizer_pass = canonical_state == "pass" or offline_status == "pass"
    hv["offline_sanitizer"] = "pass" if sanitizer_pass else "fail"
    hv["asan"] = "none" if sanitizer_pass else ""
    hv["ubsan"] = "none" if sanitizer_pass else ""
    for key in hv["fault_injection"]:
        hv["fault_injection"][key] = sanitizer_pass

    if canonical_state == "blocked":
        blockers.append("canonical host test blocked by external dependency/network access")
    elif canonical_state != "pass":
        blockers.append("canonical host test failed")
    if canonical_state != "pass" and offline_status != "pass":
        blockers.append("offline sanitizer host suite failed")
    for status, label in (
        (strict_status, "strict production compile"),
        (package_status, "package policy verifier"),
        (locks_status, "dependency lock verifier"),
        (title_status, "Title ID collision gate"),
        (diff_status, "git diff --check"),
    ):
        if status != "pass":
            blockers.append(f"{label} failed")
    return updated, blockers
