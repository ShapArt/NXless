from __future__ import annotations

import re
from typing import Any

from .schema import ATMOSPHERE_VERSION, ATMOSPHERE_COMMIT, LIBNX_VERSION, LIBNX_COMMIT, DEVKITA64, HOS, PROGRAM_ID

def validate_preflight(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != 1:
        errors.append("unsupported or missing schema_version")
        return errors

    build = record.get("build", {})
    pinned = {
        "atmosphere_version": ATMOSPHERE_VERSION,
        "atmosphere_commit": ATMOSPHERE_COMMIT,
        "libnx_version": LIBNX_VERSION,
        "libnx_commit": LIBNX_COMMIT,
        "devkitA64": DEVKITA64,
        "hos": HOS,
        "program_id": PROGRAM_ID,
    }
    for key, expected in pinned.items():
        if build.get(key) != expected:
            errors.append(f"build.{key} must be {expected}")
    commit = build.get("nxless_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("build.nxless_commit must be a full 40-hex git commit")
    if build.get("source_tree_clean") is not True:
        errors.append("source tree was dirty when evidence record was created")

    hv = record.get("host_verification", {})
    for key in ("strict_compile", "package_verifier", "dependency_lock_verifier", "title_id_collision_gate", "git_diff_check"):
        if hv.get(key) is not True:
            errors.append(f"host_verification.{key} is not PASS")
    canonical = hv.get("canonical_host_test", "")
    if canonical == "pass":
        fi = hv.get("fault_injection", {})
        for key in (
            "connect_failures_10000",
            "teardown_zero",
            "backend_disappearance_typed",
            "sleep_wake_preserves_state",
            "diagnostics_denial_safe",
        ):
            if fi.get(key) is not True:
                errors.append(f"fault_injection.{key} is not PASS")
        if hv.get("offline_sanitizer") != "pass":
            errors.append("sanitizer-enabled host suite is not PASS")
        if hv.get("asan") != "none" or hv.get("ubsan") != "none":
            errors.append("ASan/UBSan diagnostics are not recorded as none")
    elif canonical == "blocked":
        reason = str(hv.get("canonical_block_reason", ""))
        reason_lines = [line.strip() for line in reason.splitlines() if line.strip()]
        preferred = next((line for line in reason_lines if "could not resolve host" in line.lower()), "")
        summary = preferred or (reason_lines[-1] if reason_lines else "external dependency unavailable")
        errors.append(f"canonical make host-test is BLOCKED: {summary[:300]}")
        if hv.get("offline_sanitizer") == "fail":
            errors.append("offline sanitizer host suite is not PASS")
    else:
        errors.append("canonical make host-test is not PASS")

    return errors
