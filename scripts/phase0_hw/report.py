from __future__ import annotations

from pathlib import Path
from typing import Any

from .schema import (
    ATMOSPHERE_FULL_COMMIT,
    ATMOSPHERE_VERSION,
    ATMOSPHERE_COMMIT,
    GCC_VERSION_PREFIX,
    HOS,
    LIBNX_PACKAGE,
    REQUIRED_COUNTS,
    _attempt,
    new_record,
)
from .validate import validate_record


def render_markdown(record: dict[str, Any], level: str = "phase0") -> str:
    errors = validate_record(record, level=level)
    verdict = "PASS" if not errors else "FAIL"
    verdict_label = {
        "preflight": "Preflight",
        "hardware": "Hardware",
        "phase0": "Phase 0",
    }[level]
    build = record.get("build", {})
    lines = [
        "# NXless Phase 0 hardware evidence",
        "",
        f"**{verdict_label} verdict: {verdict}**",
        "",
        "## Build identity",
        "",
        f"- NXless commit: `{build.get('nxless_commit', '')}`",
        f"- Package SHA-256: `{build.get('package_sha256', '')}`",
        f"- Probe source commit: `{build.get('probe_source_commit', '')}`",
        f"- NXlessProbe SHA-256: `{build.get('probe_sha256', '')}`",
        f"- HOS target: {build.get('hos', '')}",
        f"- Atmosphère target: {build.get('atmosphere_version', '')} / `{build.get('atmosphere_commit', '')}`",
        f"- observed Atmosphère commit: `{build.get('observed_atmosphere_commit', '')}`",
        f"- libnx source: {build.get('libnx_version', '')} / `{build.get('libnx_commit', '')}`",
        f"- admitted devkitA64: {build.get('devkitA64', '')}",
        f"- observed devkitA64 package: `{build.get('observed_devkitA64_package', '')}`",
        f"- observed GCC: `{build.get('observed_gcc_version', '')}`",
        f"- observed libnx package: `{build.get('observed_libnx_package', '')}`",
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
        f"- session admission churn: {len(record.get('session_admission', {}).get('attempts', []))}/{REQUIRED_COUNTS['session_admission']} minimum",
        f"- recent logs secret-free: {record.get('diagnostics', {}).get('recent_logs_secret_free')}",
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
    synthetic_commit = "9" * 40
    record["build"].update(
        {
            "nxless_commit": synthetic_commit,
            "package_sha256": "a" * 64,
            "probe_source_commit": synthetic_commit,
            "probe_sha256": "b" * 64,
            "source_tree_clean": True,
            "switch_toolchain_verified": True,
            "atmosphere_source_verified": True,
            "clean_switch_build": True,
            "clean_probe_build": True,
            "observed_devkitA64_package": "devkitA64 r30-1",
            "observed_gcc_version": GCC_VERSION_PREFIX,
            "observed_libnx_package": LIBNX_PACKAGE,
            "observed_atmosphere_commit": ATMOSPHERE_FULL_COMMIT,
        }
    )
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
        {
            "model": "HAC-001 synthetic",
            "hos": HOS,
            "atmosphere_version": ATMOSPHERE_VERSION,
            "atmosphere_commit": ATMOSPHERE_COMMIT,
            "network": "synthetic LAN",
            "hbmenu_tcp_baseline": True,
            "hbmenu_udp_baseline": True,
        }
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
            "wifi_ethernet": {"available": False, "attempts": 0, "passes": 0},
            "ethernet_wifi": {"available": False, "attempts": 0, "passes": 0},
            "app_launch_close": {"attempts": 20, "passes": 20},
        }
    )
    record["session_admission"]["attempts"] = [
        {"completed": True, "sm_ack_abort": False, "notes": ""},
        {"completed": True, "sm_ack_abort": False, "notes": ""},
    ]
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
    record["diagnostics"].update({"recent_logs_secret_free": True, "notes": "synthetic"})
    record["review"] = {
        "reviewer": "synthetic-reviewer",
        "date": "2026-09-04",
        "critical_unresolved": 0,
        "important_unresolved": 0,
    }
    return record
