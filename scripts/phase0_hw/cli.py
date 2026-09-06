from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Callable

from .record_commands import (
    _cmd_record_boot,
    _cmd_record_lifecycle,
    _cmd_record_network,
    _cmd_record_app,
    _cmd_record_directory_recovery,
    _cmd_record_resources,
    _cmd_record_review,
    _cmd_record_console,
    _cmd_record_session_admission,
    _cmd_record_diagnostics,
    _cmd_record_ethernet_availability,
    _cmd_record_failure,
)
from .gate_commands import (
    _cmd_record_host,
    _cmd_record_build,
    _cmd_record_probe_build,
    _cmd_new_record,
    _cmd_check,
    _cmd_echo,
    _cmd_preflight,
)


def main(
    *,
    collect_host_verification: Callable[..., Any],
    record_switch_build: Callable[..., Any],
    record_probe_build: Callable[..., Any],
    preflight: Callable[..., Any],
) -> int:
    parser = argparse.ArgumentParser(description="NXless Phase 0 hardware-test helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new-record", help="create a pinned machine-readable hardware record")
    p_new.add_argument("--repo", type=Path, default=Path.cwd())
    p_new.add_argument("--output", type=Path, required=True)
    p_new.set_defaults(func=_cmd_new_record)

    p_check = sub.add_parser("check", help="validate a hardware record and emit Markdown evidence")
    p_check.add_argument("--record", type=Path, required=True)
    p_check.add_argument("--level", choices=("preflight", "hardware", "phase0"), default="phase0")
    p_check.add_argument("--markdown", type=Path)
    p_check.set_defaults(func=_cmd_check)

    p_host = sub.add_parser("record-host", help="run and atomically record machine-observed host verification gates")
    p_host.add_argument("--record", type=Path, required=True)
    p_host.add_argument("--repo", type=Path, default=Path.cwd())
    p_host.set_defaults(func=lambda args: _cmd_record_host(args, collect_host_verification))

    p_build = sub.add_parser("record-build", help="perform and atomically record the pinned clean Switch package build")
    p_build.add_argument("--record", type=Path, required=True)
    p_build.add_argument("--repo", type=Path, default=Path.cwd())
    p_build.add_argument("--builder", default=os.environ.get("USER", ""))
    p_build.set_defaults(func=lambda args: _cmd_record_build(args, record_switch_build))

    p_probe = sub.add_parser("record-probe-build", help="build and bind the test-only NXlessProbe.nro to this evidence record")
    p_probe.add_argument("--record", type=Path, required=True)
    p_probe.add_argument("--repo", type=Path, default=Path.cwd())
    p_probe.set_defaults(func=lambda args: _cmd_record_probe_build(args, record_probe_build))

    p_console = sub.add_parser("record-console", help="record observed console identity and HBMenu network baseline")
    p_console.add_argument("--record", type=Path, required=True)
    p_console.add_argument("--model", required=True)
    p_console.add_argument("--hos", required=True)
    p_console.add_argument("--atmosphere-version", required=True)
    p_console.add_argument("--atmosphere-commit", required=True)
    p_console.add_argument("--sd-filesystem-capacity", default="")
    p_console.add_argument("--network", required=True)
    p_console.add_argument("--hbmenu-tcp-baseline", choices=("pass", "fail"), required=True)
    p_console.add_argument("--hbmenu-udp-baseline", choices=("pass", "fail"), required=True)
    p_console.set_defaults(func=_cmd_record_console)

    p_boot = sub.add_parser("record-boot", help="append one cold-boot result")
    p_boot.add_argument("--record", type=Path, required=True)
    p_boot.add_argument("--mode", choices=("disable", "mitm"), required=True)
    p_boot.add_argument("--cold-boot", choices=("pass", "fail"), required=True)
    p_boot.add_argument("--home", choices=("pass", "fail"), required=True)
    p_boot.add_argument("--network", choices=("pass", "fail"), required=True)
    p_boot.add_argument("--ctl-status", default="")
    p_boot.add_argument("--notes", default="")
    p_boot.set_defaults(func=_cmd_record_boot)

    p_life = sub.add_parser("record-lifecycle", help="append one lifecycle transition result")
    p_life.add_argument("--record", type=Path, required=True)
    p_life.add_argument(
        "--kind",
        choices=("home_resume", "sleep_wake", "wifi_cycle", "ap_change", "airplane_wifi", "wifi_ethernet", "ethernet_wifi", "app_launch_close"),
        required=True,
    )
    p_life.add_argument("--result", choices=("pass", "fail"), required=True)
    p_life.set_defaults(func=_cmd_record_lifecycle)

    p_eth = sub.add_parser("record-ethernet-availability", help="record whether bidirectional Wi-Fi/Ethernet transition testing is available")
    p_eth.add_argument("--record", type=Path, required=True)
    p_eth.add_argument("--available", choices=("yes", "no"), required=True)
    p_eth.set_defaults(func=_cmd_record_ethernet_availability)

    p_session = sub.add_parser("record-session-admission", help="append one bsd:u client/session admission churn result")
    p_session.add_argument("--record", type=Path, required=True)
    p_session.add_argument("--result", choices=("pass", "fail"), required=True)
    p_session.add_argument("--sm-ack-abort", choices=("yes", "no"), required=True)
    p_session.add_argument("--notes", default="")
    p_session.set_defaults(func=_cmd_record_session_admission)

    p_net = sub.add_parser("record-network", help="record TCP or UDP passthrough evidence")
    p_net.add_argument("--record", type=Path, required=True)
    p_net.add_argument("--protocol", choices=("tcp", "udp"), required=True)
    p_net.add_argument("--target", required=True)
    p_net.add_argument("--concurrent", type=int, required=True)
    p_net.add_argument("--baseline", choices=("pass", "fail"), required=True)
    p_net.add_argument("--nxless", choices=("pass", "fail"), required=True)
    p_net.set_defaults(func=_cmd_record_network)

    p_app = sub.add_parser("record-app", help="record one real application smoke result")
    p_app.add_argument("--record", type=Path, required=True)
    p_app.add_argument("--title", required=True)
    p_app.add_argument("--version", default="")
    p_app.add_argument("--baseline", choices=("pass", "fail"), required=True)
    p_app.add_argument("--nxless", choices=("pass", "fail"), required=True)
    p_app.add_argument("--notes", default="")
    p_app.set_defaults(func=_cmd_record_app)

    p_rec = sub.add_parser("record-recovery", help="record directory-removal recovery result")
    p_rec.add_argument("--record", type=Path, required=True)
    p_rec.add_argument("--powered-off", choices=("pass", "fail"), required=True)
    p_rec.add_argument("--removed-only-program-dir", choices=("pass", "fail"), required=True)
    p_rec.add_argument("--boot", choices=("pass", "fail"), required=True)
    p_rec.add_argument("--network", choices=("pass", "fail"), required=True)
    p_rec.set_defaults(func=_cmd_record_directory_recovery)

    p_res = sub.add_parser("record-resources", help="record bounded-resource observations")
    p_res.add_argument("--record", type=Path, required=True)
    p_res.add_argument("--private-heap-bytes", type=int, required=True)
    p_res.add_argument("--peak-heap-bytes", type=int, required=True)
    p_res.add_argument("--peak-clients", type=int, required=True)
    p_res.add_argument("--peak-sockets", type=int, required=True)
    p_res.add_argument("--handle-count", type=int)
    p_res.add_argument("--registry-leak-detected", choices=("yes", "no"), required=True)
    p_res.add_argument("--unbounded-growth-detected", choices=("yes", "no"), required=True)
    p_res.set_defaults(func=_cmd_record_resources)

    p_diag = sub.add_parser("record-diagnostics", help="record review of recent sanitized diagnostics/logs")
    p_diag.add_argument("--record", type=Path, required=True)
    p_diag.add_argument("--recent-logs-secret-free", choices=("yes", "no"), required=True)
    p_diag.add_argument("--notes", default="")
    p_diag.set_defaults(func=_cmd_record_diagnostics)

    p_failure = sub.add_parser("record-failure", help="append a blocking crash/fatal/failure observation")
    p_failure.add_argument("--record", type=Path, required=True)
    p_failure.add_argument("--kind", required=True)
    p_failure.add_argument("--details", required=True)
    p_failure.set_defaults(func=_cmd_record_failure)

    p_review = sub.add_parser("record-review", help="record independent code-review result")
    p_review.add_argument("--record", type=Path, required=True)
    p_review.add_argument("--reviewer", required=True)
    p_review.add_argument("--date", required=True)
    p_review.add_argument("--critical", type=int, required=True)
    p_review.add_argument("--important", type=int, required=True)
    p_review.set_defaults(func=_cmd_record_review)

    p_echo = sub.add_parser("echo-server", help="run TCP and UDP echo endpoints for passthrough tests")
    p_echo.add_argument("--host", default="0.0.0.0")
    p_echo.add_argument("--tcp-port", type=int, default=5001)
    p_echo.add_argument("--udp-port", type=int, default=5002)
    p_echo.set_defaults(func=_cmd_echo)

    p_pre = sub.add_parser("preflight", help="check whether this host can build the Switch sysmodule")
    p_pre.add_argument("--repo", type=Path, default=Path.cwd())
    p_pre.set_defaults(func=lambda args: _cmd_preflight(args, preflight))

    args = parser.parse_args()
    return int(args.func(args))
