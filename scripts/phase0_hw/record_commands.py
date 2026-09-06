from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import append_boot, add_lifecycle_attempt, append_session_admission


def _read_record(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_record_atomic(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _pass_fail(value: str) -> bool:
    if value == "pass":
        return True
    if value == "fail":
        return False
    raise ValueError(value)


def _yes_no(value: str) -> bool:
    if value == "yes":
        return True
    if value == "no":
        return False
    raise ValueError(value)


def _cmd_record_boot(args) -> int:
    record = _read_record(args.record)
    append_boot(
        record,
        args.mode,
        cold_boot=_pass_fail(args.cold_boot),
        home_reached=_pass_fail(args.home),
        networking=_pass_fail(args.network),
        ctl_status=args.ctl_status,
        notes=args.notes,
    )
    _write_record_atomic(args.record, record)
    target = record["recovery"]["disable_flag_boots"] if args.mode == "disable" else record["transparent_mitm"]["cold_boots"]
    print(f"Recorded {args.mode} boot attempt #{len(target)}")
    return 0


def _cmd_record_lifecycle(args) -> int:
    record = _read_record(args.record)
    add_lifecycle_attempt(record, args.kind, passed=_pass_fail(args.result))
    _write_record_atomic(args.record, record)
    item = record["lifecycle"][args.kind]
    print(f"Recorded {args.kind}: {item['passes']}/{item['attempts']} PASS")
    return 0


def _cmd_record_network(args) -> int:
    record = _read_record(args.record)
    item = record["network"][args.protocol]
    item.update(
        {
            "target": args.target,
            "concurrent_sockets": args.concurrent,
            "baseline_ok": _pass_fail(args.baseline),
            "nxless_ok": _pass_fail(args.nxless),
        }
    )
    _write_record_atomic(args.record, record)
    print(f"Recorded {args.protocol.upper()} passthrough evidence")
    return 0


def _cmd_record_app(args) -> int:
    record = _read_record(args.record)
    record["applications"].append(
        {
            "title": args.title,
            "version": args.version,
            "baseline_ok": _pass_fail(args.baseline),
            "nxless_ok": _pass_fail(args.nxless),
            "notes": args.notes,
        }
    )
    _write_record_atomic(args.record, record)
    print(f"Recorded application evidence: {args.title}")
    return 0


def _cmd_record_directory_recovery(args) -> int:
    record = _read_record(args.record)
    record["recovery"]["directory_removal"] = {
        "powered_off": _pass_fail(args.powered_off),
        "removed_only_program_dir": _pass_fail(args.removed_only_program_dir),
        "boot_ok": _pass_fail(args.boot),
        "networking_restored": _pass_fail(args.network),
    }
    _write_record_atomic(args.record, record)
    print("Recorded directory-removal recovery evidence")
    return 0


def _cmd_record_resources(args) -> int:
    record = _read_record(args.record)
    record["resources"].update(
        {
            "private_heap_bytes": args.private_heap_bytes,
            "peak_heap_bytes": args.peak_heap_bytes,
            "peak_clients": args.peak_clients,
            "peak_sockets": args.peak_sockets,
            "handle_count": args.handle_count,
            "registry_leak_detected": _yes_no(args.registry_leak_detected),
            "unbounded_growth_detected": _yes_no(args.unbounded_growth_detected),
        }
    )
    _write_record_atomic(args.record, record)
    print("Recorded resource evidence")
    return 0


def _cmd_record_review(args) -> int:
    record = _read_record(args.record)
    record["review"] = {
        "reviewer": args.reviewer,
        "date": args.date,
        "critical_unresolved": args.critical,
        "important_unresolved": args.important,
    }
    _write_record_atomic(args.record, record)
    print("Recorded independent review evidence")
    return 0


def _cmd_record_console(args) -> int:
    record = _read_record(args.record)
    record["console"].update(
        {
            "model": args.model,
            "hos": args.hos,
            "atmosphere_version": args.atmosphere_version,
            "atmosphere_commit": args.atmosphere_commit,
            "sd_filesystem_capacity": args.sd_filesystem_capacity,
            "network": args.network,
            "hbmenu_tcp_baseline": _pass_fail(args.hbmenu_tcp_baseline),
            "hbmenu_udp_baseline": _pass_fail(args.hbmenu_udp_baseline),
        }
    )
    _write_record_atomic(args.record, record)
    print("Recorded observed console identity and HBMenu baseline")
    return 0


def _cmd_record_session_admission(args) -> int:
    record = _read_record(args.record)
    append_session_admission(
        record,
        completed=_pass_fail(args.result),
        sm_ack_abort=_yes_no(args.sm_ack_abort),
        notes=args.notes,
    )
    _write_record_atomic(args.record, record)
    print(f"Recorded session-admission attempt #{len(record['session_admission']['attempts'])}")
    return 0


def _cmd_record_diagnostics(args) -> int:
    record = _read_record(args.record)
    record["diagnostics"].update(
        {
            "recent_logs_secret_free": _yes_no(args.recent_logs_secret_free),
            "notes": args.notes,
        }
    )
    _write_record_atomic(args.record, record)
    print("Recorded sanitized diagnostics review")
    return 0


def _cmd_record_ethernet_availability(args) -> int:
    record = _read_record(args.record)
    available = _yes_no(args.available)
    for kind in ("wifi_ethernet", "ethernet_wifi"):
        item = record["lifecycle"][kind]
        item["available"] = available
        if not available:
            item["attempts"] = 0
            item["passes"] = 0
    _write_record_atomic(args.record, record)
    print(f"Recorded Ethernet transition hardware availability: {'yes' if available else 'no'}")
    return 0


def _cmd_record_failure(args) -> int:
    record = _read_record(args.record)
    record["failures"].append({"kind": args.kind, "details": args.details})
    _write_record_atomic(args.record, record)
    print(f"Recorded blocking failure: {args.kind}")
    return 0
