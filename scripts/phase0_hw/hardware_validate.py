from __future__ import annotations

import re
from typing import Any

from .schema import (
    ATMOSPHERE_VERSION,
    ATMOSPHERE_COMMIT,
    ATMOSPHERE_FULL_COMMIT,
    DEVKITA64_PACKAGE_PATTERN,
    GCC_VERSION_PREFIX,
    HOS,
    LIBNX_PACKAGE,
    REQUIRED_COUNTS,
)


def _all_attempts_ok(
    attempts: list[dict[str, Any]], label: str, errors: list[str], expected_ctl_status: str | None = None
) -> None:
    for i, attempt in enumerate(attempts, start=1):
        for key in ("cold_boot", "home_reached", "networking"):
            if attempt.get(key) is not True:
                errors.append(f"{label} attempt {i}: {key} is not PASS")
        if expected_ctl_status is not None and attempt.get("ctl_status") != expected_ctl_status:
            errors.append(
                f"{label} attempt {i}: nxl:ctl mode must be {expected_ctl_status}, got {attempt.get('ctl_status')!r}"
            )


def _check_counter(record: dict[str, Any], key: str, required: int, label: str, errors: list[str]) -> None:
    item = record["lifecycle"].get(key, {})
    attempts = int(item.get("attempts", 0) or 0)
    passes = int(item.get("passes", 0) or 0)
    if attempts < required:
        errors.append(f"{label} requires {required} attempts; recorded {attempts}")
    if passes != attempts:
        errors.append(f"{label}: passes ({passes}) must equal attempts ({attempts})")


def validate_hardware(record: dict[str, Any], errors: list[str]) -> None:
    build = record.get("build", {})
    if build.get("switch_toolchain_verified") is not True:
        errors.append("Switch toolchain identity was not machine-verified")
    if build.get("atmosphere_source_verified") is not True:
        errors.append("Atmosphere source identity was not machine-verified")
    if build.get("clean_switch_build") is not True:
        errors.append("clean Switch build is not PASS")

    observed_devkit = str(build.get("observed_devkitA64_package", ""))
    if re.fullmatch(DEVKITA64_PACKAGE_PATTERN, observed_devkit) is None:
        errors.append("observed devkitA64 package does not match admitted r30")
    observed_gcc = str(build.get("observed_gcc_version", ""))
    if not observed_gcc.startswith(GCC_VERSION_PREFIX):
        errors.append(f"observed GCC version must start with {GCC_VERSION_PREFIX}")
    if build.get("observed_libnx_package") != LIBNX_PACKAGE:
        errors.append(f"observed libnx package must be {LIBNX_PACKAGE}")
    if build.get("observed_atmosphere_commit") != ATMOSPHERE_FULL_COMMIT:
        errors.append("observed Atmosphere commit does not match admitted 1.11.2 source")

    package_sha = build.get("package_sha256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", package_sha):
        errors.append("build.package_sha256 must be 64 lowercase hex characters")

    console = record.get("console", {})
    if console.get("hos") != HOS:
        errors.append(f"console HOS must be {HOS}")
    if console.get("atmosphere_version") != ATMOSPHERE_VERSION or console.get("atmosphere_commit") != ATMOSPHERE_COMMIT:
        errors.append("console Atmosphere identity does not match pinned stack")
    if not console.get("model"):
        errors.append("console model/revision is missing")
    if console.get("hbmenu_tcp_baseline") is not True:
        errors.append("HBMenu TCP baseline is not PASS")
    if console.get("hbmenu_udp_baseline") is not True:
        errors.append("HBMenu UDP baseline is not PASS")

    recovery = record.get("recovery", {})
    disable_boots = recovery.get("disable_flag_boots", [])
    if len(disable_boots) < REQUIRED_COUNTS["disable_flag_boots"]:
        errors.append(
            f"disable.flag cold boots require {REQUIRED_COUNTS['disable_flag_boots']}; recorded {len(disable_boots)}"
        )
    _all_attempts_ok(disable_boots, "disable.flag boot", errors, "SafeDisabled")
    dr = recovery.get("directory_removal", {})
    for key in ("powered_off", "removed_only_program_dir", "boot_ok", "networking_restored"):
        if dr.get(key) is not True:
            errors.append(f"directory-removal recovery.{key} is not PASS")

    mitm_boots = record.get("transparent_mitm", {}).get("cold_boots", [])
    if len(mitm_boots) < REQUIRED_COUNTS["transparent_mitm_boots"]:
        errors.append(
            f"transparent MITM cold boots require {REQUIRED_COUNTS['transparent_mitm_boots']}; recorded {len(mitm_boots)}"
        )
    _all_attempts_ok(mitm_boots, "transparent MITM boot", errors, "DisconnectedPassthrough")

    network = record.get("network", {})
    for proto in ("tcp", "udp"):
        item = network.get(proto, {})
        if item.get("baseline_ok") is not True or item.get("nxless_ok") is not True:
            errors.append(f"{proto.upper()} baseline/NXless passthrough is not PASS")
        if int(item.get("concurrent_sockets", 0) or 0) < 1:
            errors.append(f"{proto.upper()} concurrent socket count is missing")

    apps = record.get("applications", [])
    good_apps = [a for a in apps if a.get("title") and a.get("baseline_ok") is True and a.get("nxless_ok") is True]
    distinct_apps = {(a.get("title"), a.get("version", "")) for a in good_apps}
    if len(distinct_apps) < 2:
        errors.append("at least two distinct real network applications/games must match baseline")

    _check_counter(record, "sleep_wake", REQUIRED_COUNTS["sleep_wake"], "sleep/wake", errors)
    _check_counter(record, "wifi_cycle", REQUIRED_COUNTS["wifi_cycle"], "Wi-Fi off/on", errors)
    _check_counter(record, "ap_change", REQUIRED_COUNTS["ap_change"], "AP change", errors)
    _check_counter(record, "app_launch_close", REQUIRED_COUNTS["app_launch_close"], "app launch/close", errors)
    _check_counter(record, "home_resume", 1, "HOME/resume", errors)
    _check_counter(record, "airplane_wifi", 1, "airplane mode/Wi-Fi", errors)
    for key, label in (("wifi_ethernet", "Wi-Fi/Ethernet"), ("ethernet_wifi", "Ethernet/Wi-Fi")):
        item = record["lifecycle"].get(key, {})
        if item.get("available"):
            _check_counter(record, key, 1, label, errors)

    resources = record.get("resources", {})
    for key in ("private_heap_bytes", "peak_heap_bytes", "peak_clients", "peak_sockets"):
        value = resources.get(key)
        if value is None:
            errors.append(f"resources.{key} is missing")
        elif not isinstance(value, int) or value < 0:
            errors.append(f"resources.{key} must be non-negative")
    private_heap = resources.get("private_heap_bytes")
    if isinstance(private_heap, int) and private_heap > 6 * 1024 * 1024:
        errors.append("private heap exceeds Phase 0 target of 6 MiB")
    if isinstance(private_heap, int) and private_heap > 8 * 1024 * 1024:
        errors.append("private heap exceeds hard 8 MiB architecture-review ceiling")
    if resources.get("registry_leak_detected") is not False:
        errors.append("registry leak check is not explicitly false")
    if resources.get("unbounded_growth_detected") is not False:
        errors.append("unbounded growth check is not explicitly false")

    if record.get("failures"):
        errors.append("record contains unresolved failures")
