from __future__ import annotations

import hashlib
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 3
ATMOSPHERE_VERSION = "1.11.2"
ATMOSPHERE_COMMIT = "5388824"
ATMOSPHERE_FULL_COMMIT = "5388824be146a89619e8d641acd64599cf1c5f62"
LIBNX_VERSION = "4.12.0"
LIBNX_COMMIT = "7644c9b26099aa2d2145bc72a21ee24190e92085"
LIBNX_PACKAGE = "libnx 4.12.0-1"
DEVKITA64 = "r30"
DEVKITA64_PACKAGE_PATTERN = r"devkitA64 r30(?:-1)?"
GCC_VERSION_PREFIX = "16.1.0"
HOS = "22.5.0"
PROGRAM_ID = "0100000000004E58"
PROBE_MAX_CONCURRENT = 16

REQUIRED_COUNTS = {
    "disable_flag_boots": 10,
    "transparent_mitm_boots": 20,
    "sleep_wake": 20,
    "wifi_cycle": 10,
    "ap_change": 5,
    "app_launch_close": 20,
    "session_admission": 2,
}


def _git(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), *args], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _attempt(ok: bool = True, ctl_status: str = "") -> dict[str, Any]:
    return {
        "cold_boot": ok,
        "home_reached": ok,
        "networking": ok,
        "ctl_status": ctl_status,
        "notes": "",
    }


def new_record(repo_root: Path) -> dict[str, Any]:
    commit = _git(repo_root, "rev-parse", "HEAD") or "UNKNOWN"
    return {
        "schema_version": SCHEMA_VERSION,
        "build": {
            "nxless_commit": commit,
            "package_sha256": "",
            "probe_source_commit": "",
            "probe_sha256": "",
            "build_date_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "builder": "",
            "atmosphere_version": ATMOSPHERE_VERSION,
            "atmosphere_commit": ATMOSPHERE_COMMIT,
            "libnx_version": LIBNX_VERSION,
            "libnx_commit": LIBNX_COMMIT,
            "devkitA64": DEVKITA64,
            "hos": HOS,
            "program_id": PROGRAM_ID,
            "source_tree_clean": _git(repo_root, "status", "--porcelain") == "",
            "switch_toolchain_verified": False,
            "atmosphere_source_verified": False,
            "clean_switch_build": False,
            "clean_probe_build": False,
            "observed_devkitA64_package": "",
            "observed_gcc_version": "",
            "observed_libnx_package": "",
            "observed_atmosphere_commit": "",
        },
        "host_verification": {
            "canonical_host_test": "",
            "canonical_block_reason": "",
            "offline_sanitizer": "",
            "asan": "",
            "ubsan": "",
            "strict_compile": False,
            "package_verifier": False,
            "dependency_lock_verifier": False,
            "title_id_collision_gate": False,
            "git_diff_check": False,
            "fault_injection": {
                "connect_failures_10000": False,
                "teardown_zero": False,
                "backend_disappearance_typed": False,
                "sleep_wake_preserves_state": False,
                "diagnostics_denial_safe": False,
            },
        },
        "console": {
            "model": "",
            "hos": "",
            "atmosphere_version": "",
            "atmosphere_commit": "",
            "sd_filesystem_capacity": "",
            "network": "",
            "hbmenu_tcp_baseline": False,
            "hbmenu_udp_baseline": False,
        },
        "recovery": {
            "disable_flag_boots": [],
            "directory_removal": {
                "powered_off": False,
                "removed_only_program_dir": False,
                "boot_ok": False,
                "networking_restored": False,
            },
        },
        "transparent_mitm": {"cold_boots": []},
        "network": {
            "tcp": {"target": "", "concurrent_sockets": 0, "baseline_ok": False, "nxless_ok": False},
            "udp": {"target": "", "concurrent_sockets": 0, "baseline_ok": False, "nxless_ok": False},
        },
        "applications": [],
        "lifecycle": {
            "home_resume": {"attempts": 0, "passes": 0},
            "sleep_wake": {"attempts": 0, "passes": 0},
            "wifi_cycle": {"attempts": 0, "passes": 0},
            "ap_change": {"attempts": 0, "passes": 0},
            "airplane_wifi": {"attempts": 0, "passes": 0},
            "wifi_ethernet": {"available": None, "attempts": 0, "passes": 0},
            "ethernet_wifi": {"available": None, "attempts": 0, "passes": 0},
            "app_launch_close": {"attempts": 0, "passes": 0},
        },
        "session_admission": {"attempts": []},
        "resources": {
            "private_heap_bytes": None,
            "peak_heap_bytes": None,
            "peak_clients": None,
            "peak_sockets": None,
            "handle_count": None,
            "registry_leak_detected": None,
            "unbounded_growth_detected": None,
        },
        "diagnostics": {
            "recent_logs_secret_free": None,
            "notes": "",
        },
        "failures": [],
        "review": {
            "reviewer": "",
            "date": "",
            "critical_unresolved": None,
            "important_unresolved": None,
        },
    }


def append_boot(
    record: dict[str, Any],
    mode: str,
    *,
    cold_boot: bool,
    home_reached: bool,
    networking: bool,
    ctl_status: str = "",
    notes: str = "",
) -> None:
    attempt = {
        "cold_boot": cold_boot,
        "home_reached": home_reached,
        "networking": networking,
        "ctl_status": ctl_status,
        "notes": notes,
    }
    if mode == "disable":
        record["recovery"]["disable_flag_boots"].append(attempt)
    elif mode == "mitm":
        record["transparent_mitm"]["cold_boots"].append(attempt)
    else:
        raise ValueError(f"unknown boot mode: {mode}")


def add_lifecycle_attempt(record: dict[str, Any], kind: str, *, passed: bool) -> None:
    if kind not in record["lifecycle"]:
        raise ValueError(f"unknown lifecycle kind: {kind}")
    item = record["lifecycle"][kind]
    if "available" in item:
        if item.get("available") is not True:
            raise ValueError(f"lifecycle kind {kind} is not recorded as available")
    item["attempts"] = int(item.get("attempts", 0) or 0) + 1
    if passed:
        item["passes"] = int(item.get("passes", 0) or 0) + 1


def append_session_admission(
    record: dict[str, Any], *, completed: bool, sm_ack_abort: bool, notes: str = ""
) -> None:
    record["session_admission"]["attempts"].append(
        {"completed": completed, "sm_ack_abort": sm_ack_abort, "notes": notes}
    )
