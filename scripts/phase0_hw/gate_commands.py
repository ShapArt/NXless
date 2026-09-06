from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable

from .echo import EchoServer
from .record import new_record, render_markdown, validate_record
from .record_commands import _read_record, _write_record_atomic


def _cmd_record_host(args, collect_host_verification: Callable[..., Any]) -> int:
    record = _read_record(args.record)
    updated, blockers = collect_host_verification(record, args.repo.resolve())
    _write_record_atomic(args.record, updated)
    if blockers:
        for blocker in blockers:
            print(f"BLOCKED: {blocker}")
        return 2
    print("Recorded machine-observed host verification: PASS")
    return 0


def _cmd_record_build(args, record_switch_build: Callable[..., Any]) -> int:
    record = _read_record(args.record)
    updated, blockers = record_switch_build(record, args.repo.resolve(), builder=args.builder)
    _write_record_atomic(args.record, updated)
    if blockers:
        for blocker in blockers:
            print(f"BLOCKED: {blocker}")
        return 2
    print(f"Recorded clean Switch build: {updated['build']['package_sha256']}")
    return 0


def _cmd_record_probe_build(args, record_probe_build: Callable[..., Any]) -> int:
    record = _read_record(args.record)
    updated, blockers = record_probe_build(record, args.repo.resolve())
    _write_record_atomic(args.record, updated)
    if blockers:
        for blocker in blockers:
            print(f"BLOCKED: {blocker}")
        return 2
    print(f"Recorded clean hardware probe build: {updated['build']['probe_sha256']}")
    return 0


def _cmd_new_record(args) -> int:
    repo = args.repo.resolve()
    record = new_record(repo)
    _write_record_atomic(args.output, record)
    print(f"Created hardware record: {args.output}")
    return 0


def _cmd_check(args) -> int:
    record = json.loads(args.record.read_text(encoding="utf-8"))
    errors = validate_record(record, level=args.level)
    text = render_markdown(record, level=args.level)
    if args.markdown:
        args.markdown.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not errors else 1


def _cmd_echo(args) -> int:
    server = EchoServer(args.host, args.tcp_port, args.udp_port)
    server.start()
    print(f"NXless Phase 0 echo server: TCP {args.host}:{server.tcp_port}, UDP {args.host}:{server.udp_port}")
    print("Press Ctrl-C to stop.")
    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        return 0
    finally:
        server.stop()


def _cmd_preflight(args, preflight: Callable[..., Any]) -> int:
    info = preflight(args.repo.resolve())
    print(json.dumps(info, indent=2))
    if not info["ready"]:
        for item in info["blockers"]:
            print(f"BLOCKED: {item}")
        return 2
    print("Hardware build preflight: READY")
    return 0
