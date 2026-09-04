from __future__ import annotations

from pathlib import Path
from typing import Any

from .schema import REQUIRED_COUNTS, new_record, _attempt
from .validate import validate_record

def render_markdown(record: dict[str, Any], level: str = "phase0") -> str:
    errors = validate_record(record, level=level)
    verdict = "PASS" if not errors else "FAIL"
    build = record.get("build", {})
    lines = [
        "# NXless Phase 0 hardware evidence",
        "",
        f"**Phase 0 verdict: {verdict}**",
        "",
        "## Build identity",
        "",
        f"- NXless commit: `{build.get('nxless_commit', '')}`",
        f"- Package SHA-256: `{build.get('package_sha256', '')}`",
        f"- HOS: {build.get('hos', '')}",
        f"- Atmosphère: {build.get('atmosphere_version', '')} / `{build.get('atmosphere_commit', '')}`",
        f"- libnx: {build.get('libnx_version', '')} / `{build.get('libnx_commit', '')}`",
        f"- devkitA64: {build.get('devkitA64', '')}",
        f"- Program ID: `{build.get('program_id', '')}`",
        "",
        "## Evidence counts",
        "",
        f"- disable.flag cold boots: {len(record.get('recovery', {}).get('disable_flag_boots', []))}/{REQUIRED_COUNTS['disable_flag_boots']}",
        f"- transparent MITM cold boots: {len(record.get('transparent_mitm', {}).get('cold_boots', []))}/{REQUIRED_COUNTS['transparent_mitm_boots']}",
        f"- sleep/wake: {record.get('lifecycle', {}).get('sleep_wake', {}).get('passes', 0)}/{REQUIRED_COUNTS['sleep_wake']}",
        f"- Wi-Fi off/on: {record.get('lifecycle', {}).get('wifi_cycle', {}).get('passes', 0)}/{REQUIRED_COUNTS['wifi_cycle']}",
        f"- AP changes: {record.get('lifecycle', {}).get('ap_change', {}).get('passes', 0)}/{REQUIRED_COUNTS['ap_change']}",
        f"- app launch/close: {record.get('lifecycle', {}).get('app_launch_close', {}).get('passes', 0)}/{REQUIRED_COUNTS['app_launch_close']}",
        "",
    ]
    if errors:
        lines.extend(["## Blocking findings", ""])
        lines.extend(f"- {e}" for e in errors)
    else:
        lines.extend(["## Blocking findings", "", "None."])
    return "\n".join(lines) + "\n"


def synthetic_complete_record() -> dict[str, Any]:
    record = new_record(Path.cwd())
    record["build"].update({"nxless_commit": "9" * 40, "package_sha256": "a" * 64, "source_tree_clean": True, "switch_toolchain_verified": True, "atmosphere_source_verified": True, "clean_switch_build": True})
    hv = record["host_verification"]
    hv.update(
        {
            "canonical_host_test": "pass",
            "offline_sanitizer": "pass",
            "asan": "none",
            "ubsan": "none",
            "strict_compile": True,
            "package_verifier": True,
            "dependency_lock_verifier": True,
            "title_id_collision_gate": True,
            "git_diff_check": True,
        }
    )
    for key in hv["fault_injection"]:
        hv["fault_injection"][key] = True
    record["console"].update(
        {"model": "HAC-001 synthetic", "hbmenu_tcp_baseline": True, "hbmenu_udp_baseline": True}
    )
    record["recovery"]["disable_flag_boots"] = [_attempt(True, "SafeDisabled") for _ in range(10)]
    record["recovery"]["directory_removal"] = {
        "powered_off": True,
        "removed_only_program_dir": True,
        "boot_ok": True,
        "networking_restored": True,
    }
    record["transparent_mitm"]["cold_boots"] = [_attempt(True, "DisconnectedPassthrough") for _ in range(20)]
    record["network"]["tcp"].update({"target": "127.0.0.1:5001", "concurrent_sockets": 4, "baseline_ok": True, "nxless_ok": True})
    record["network"]["udp"].update({"target": "127.0.0.1:5002", "concurrent_sockets": 4, "baseline_ok": True, "nxless_ok": True})
    record["applications"] = [
        {"title": "Synthetic App A", "version": "1", "baseline_ok": True, "nxless_ok": True},
        {"title": "Synthetic App B", "version": "1", "baseline_ok": True, "nxless_ok": True},
    ]
    record["lifecycle"].update(
        {
            "home_resume": {"attempts": 1, "passes": 1},
            "sleep_wake": {"attempts": 20, "passes": 20},
            "wifi_cycle": {"attempts": 10, "passes": 10},
            "ap_change": {"attempts": 5, "passes": 5},
            "airplane_wifi": {"attempts": 1, "passes": 1},
            "app_launch_close": {"attempts": 20, "passes": 20},
        }
    )
    record["resources"].update(
        {
            "private_heap_bytes": 2 * 1024 * 1024,
            "peak_heap_bytes": 3 * 1024 * 1024,
            "peak_clients": 4,
            "peak_sockets": 64,
            "handle_count": 80,
            "registry_leak_detected": False,
            "unbounded_growth_detected": False,
        }
    )
    record["review"] = {
        "reviewer": "synthetic-reviewer",
        "date": "2026-09-04",
        "critical_unresolved": 0,
        "important_unresolved": 0,
    }
    return record
