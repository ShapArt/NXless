from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path
from typing import Any, Callable

from .echo import EchoServer
from .record import add_lifecycle_attempt, append_boot, new_record, render_markdown, validate_record

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


def _cmd_record_boot(args: argparse.Namespace) -> int:
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


def _cmd_record_lifecycle(args: argparse.Namespace) -> int:
    record = _read_record(args.record)
    add_lifecycle_attempt(record, args.kind, passed=_pass_fail(args.result))
    _write_record_atomic(args.record, record)
    item = record["lifecycle"][args.kind]
    print(f"Recorded {args.kind}: {item['passes']}/{item['attempts']} PASS")
    return 0


def _cmd_record_network(args: argparse.Namespace) -> int:
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


def _cmd_record_app(args: argparse.Namespace) -> int:
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


def _cmd_record_directory_recovery(args: argparse.Namespace) -> int:
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


def _cmd_record_resources(args: argparse.Namespace) -> int:
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


def _cmd_record_review(args: argparse.Namespace) -> int:
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
