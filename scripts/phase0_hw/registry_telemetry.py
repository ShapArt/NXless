from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_STATUS_RE = re.compile(
    r"^clients=(\d+) client-high-water=(\d+) sockets=(\d+) "
    r"socket-high-water=(\d+) dropped-logs=(\d+) last-error=(-?\d+)$"
)


def empty_registry_telemetry() -> dict[str, Any]:
    return {
        "observed": False,
        "status_line": "",
        "active_clients": None,
        "client_high_water": None,
        "active_sockets": None,
        "socket_high_water": None,
        "dropped_logs": None,
        "last_error": None,
    }


def parse_registry_status_line(status_line: str) -> dict[str, int]:
    line = status_line.strip()
    match = _STATUS_RE.fullmatch(line)
    if match is None:
        raise ValueError(
            "expected exact nxl:ctl status line: clients=<n> client-high-water=<n> "
            "sockets=<n> socket-high-water=<n> dropped-logs=<n> last-error=<n>"
        )
    values = [int(value) for value in match.groups()]
    active_clients, client_high_water, active_sockets, socket_high_water, dropped_logs, last_error = values
    if active_clients > 0xFFFF or client_high_water > 0xFFFF:
        raise ValueError("client telemetry exceeds RuntimeStatus uint16 range")
    if active_sockets > 0xFFFF or socket_high_water > 0xFFFF:
        raise ValueError("socket telemetry exceeds RuntimeStatus uint16 range")
    if dropped_logs > 0xFFFFFFFFFFFFFFFF:
        raise ValueError("dropped-log telemetry exceeds RuntimeStatus uint64 range")
    if last_error < -0x80000000 or last_error > 0x7FFFFFFF:
        raise ValueError("last-error telemetry exceeds RuntimeStatus int32 range")
    if active_clients > client_high_water:
        raise ValueError("active clients exceed client high-water mark")
    if active_sockets > socket_high_water:
        raise ValueError("active sockets exceed socket high-water mark")
    return {
        "active_clients": active_clients,
        "client_high_water": client_high_water,
        "active_sockets": active_sockets,
        "socket_high_water": socket_high_water,
        "dropped_logs": dropped_logs,
        "last_error": last_error,
    }


def initialize_registry_telemetry(record: dict[str, Any]) -> dict[str, Any]:
    resources = record.setdefault("resources", {})
    resources.setdefault("registry_telemetry", empty_registry_telemetry())
    return record


def record_registry_status(record: dict[str, Any], status_line: str) -> dict[str, int]:
    parsed = parse_registry_status_line(status_line)
    resources = record.setdefault("resources", {})
    resources["registry_telemetry"] = {
        "observed": True,
        "status_line": status_line.strip(),
        **parsed,
    }
    resources["peak_clients"] = parsed["client_high_water"]
    resources["peak_sockets"] = parsed["socket_high_water"]
    return parsed


def bind_synthetic_registry_telemetry(record: dict[str, Any]) -> dict[str, Any]:
    resources = record.setdefault("resources", {})
    clients = int(resources.get("peak_clients", 0) or 0)
    sockets = int(resources.get("peak_sockets", 0) or 0)
    record_registry_status(
        record,
        f"clients=0 client-high-water={clients} sockets=0 socket-high-water={sockets} "
        "dropped-logs=0 last-error=0",
    )
    return record


def validate_registry_telemetry(record: dict[str, Any], errors: list[str]) -> None:
    resources = record.get("resources", {})
    telemetry = resources.get("registry_telemetry")
    if not isinstance(telemetry, dict) or telemetry.get("observed") is not True:
        errors.append("registry telemetry from nxl:ctl is missing or not observed")
        return
    status_line = telemetry.get("status_line")
    if not isinstance(status_line, str) or not status_line.strip():
        errors.append("registry telemetry status line is missing")
        return
    try:
        parsed = parse_registry_status_line(status_line)
    except ValueError as exc:
        errors.append(f"registry telemetry status line is invalid: {exc}")
        return
    for key, value in parsed.items():
        if telemetry.get(key) != value:
            errors.append(f"registry telemetry.{key} does not match captured nxl:ctl status line")
    if resources.get("peak_clients") != parsed["client_high_water"]:
        errors.append("resources.peak_clients does not match observed registry telemetry")
    if resources.get("peak_sockets") != parsed["socket_high_water"]:
        errors.append("resources.peak_sockets does not match observed registry telemetry")


def _write_record_atomic(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _cmd_record_registry_telemetry(args) -> int:
    record = json.loads(args.record.read_text(encoding="utf-8"))
    parsed = record_registry_status(record, args.status_line)
    _write_record_atomic(args.record, record)
    print(
        "Recorded nxl:ctl registry telemetry: "
        f"clients-high-water={parsed['client_high_water']} "
        f"sockets-high-water={parsed['socket_high_water']}"
    )
    return 0
