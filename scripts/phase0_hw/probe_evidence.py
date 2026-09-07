from __future__ import annotations

import ipaddress
import re
from typing import Any

from .schema import PROBE_MAX_CONCURRENT

_ECHO_RE = re.compile(
    r"^Echo target ([0-9.]+) TCP:(\d+) UDP:(\d+) concurrency:(\d+)$"
)
_SUMMARY_RE = re.compile(
    r"^Summary: ctl=(UNAVAILABLE|ERROR|PASS) tcp=(PASS|FAIL) udp=(PASS|FAIL)$"
)


def empty_probe_run() -> dict[str, Any]:
    return {
        "observed": False,
        "echo_line": "",
        "summary_line": "",
        "host": "",
        "tcp_port": None,
        "udp_port": None,
        "concurrent": None,
        "ctl": "",
        "tcp_ok": None,
        "udp_ok": None,
    }


def parse_echo_target_line(line: str) -> dict[str, Any]:
    text = line.strip()
    match = _ECHO_RE.fullmatch(text)
    if match is None:
        raise ValueError(
            "expected exact NXlessProbe echo line: Echo target <IPv4> TCP:<port> UDP:<port> concurrency:<n>"
        )
    host_text, tcp_text, udp_text, concurrent_text = match.groups()
    try:
        host = str(ipaddress.IPv4Address(host_text))
    except ipaddress.AddressValueError as exc:
        raise ValueError("echo target must be an IPv4 literal") from exc
    tcp_port = int(tcp_text)
    udp_port = int(udp_text)
    concurrent = int(concurrent_text)
    for name, port in (("TCP", tcp_port), ("UDP", udp_port)):
        if port < 1 or port > 65535:
            raise ValueError(f"{name} echo port is outside 1..65535")
    if concurrent < 1 or concurrent > PROBE_MAX_CONCURRENT:
        raise ValueError(
            f"probe concurrency must be within 1..{PROBE_MAX_CONCURRENT}"
        )
    return {
        "host": host,
        "tcp_port": tcp_port,
        "udp_port": udp_port,
        "concurrent": concurrent,
    }


def parse_probe_summary_line(line: str) -> dict[str, Any]:
    text = line.strip()
    match = _SUMMARY_RE.fullmatch(text)
    if match is None:
        raise ValueError(
            "expected exact NXlessProbe summary line: Summary: ctl=<UNAVAILABLE|ERROR|PASS> tcp=<PASS|FAIL> udp=<PASS|FAIL>"
        )
    ctl, tcp, udp = match.groups()
    return {
        "ctl": ctl,
        "tcp_ok": tcp == "PASS",
        "udp_ok": udp == "PASS",
    }


def _probe_runs(network: dict[str, Any]) -> dict[str, Any]:
    runs = network.setdefault("probe_runs", {})
    for mode in ("baseline", "nxless"):
        runs.setdefault(mode, empty_probe_run())
    return runs


def record_probe_run(
    record: dict[str, Any], mode: str, echo_line: str, summary_line: str
) -> dict[str, Any]:
    if mode not in {"baseline", "nxless"}:
        raise ValueError(f"unknown probe mode: {mode}")
    echo = parse_echo_target_line(echo_line)
    summary = parse_probe_summary_line(summary_line)
    network = record.setdefault("network", {})
    runs = _probe_runs(network)
    runs[mode] = {
        "observed": True,
        "echo_line": echo_line.strip(),
        "summary_line": summary_line.strip(),
        **echo,
        **summary,
    }

    tcp = network.setdefault("tcp", {})
    udp = network.setdefault("udp", {})
    tcp.update(
        {
            "target": f"{echo['host']}:{echo['tcp_port']}",
            "concurrent_sockets": echo["concurrent"],
        }
    )
    udp.update(
        {
            "target": f"{echo['host']}:{echo['udp_port']}",
            "concurrent_sockets": echo["concurrent"],
        }
    )
    if mode == "baseline":
        tcp["baseline_ok"] = summary["tcp_ok"]
        udp["baseline_ok"] = summary["udp_ok"]
    else:
        tcp["nxless_ok"] = summary["tcp_ok"]
        udp["nxless_ok"] = summary["udp_ok"]
    return runs[mode]


def _validate_stored_run(
    mode: str, run: Any, expected_ctl: str, errors: list[str]
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if not isinstance(run, dict) or run.get("observed") is not True:
        errors.append(f"network probe {mode} output is missing or not observed")
        return None
    echo_line = run.get("echo_line")
    summary_line = run.get("summary_line")
    if not isinstance(echo_line, str) or not isinstance(summary_line, str):
        errors.append(f"network probe {mode} captured output is missing")
        return None
    try:
        echo = parse_echo_target_line(echo_line)
        summary = parse_probe_summary_line(summary_line)
    except ValueError as exc:
        errors.append(f"network probe {mode} output is invalid: {exc}")
        return None
    for key, value in {**echo, **summary}.items():
        if run.get(key) != value:
            errors.append(
                f"network probe {mode}.{key} does not match captured NXlessProbe output"
            )
    if summary["ctl"] != expected_ctl:
        errors.append(
            f"network probe {mode} control state must be {expected_ctl}, got {summary['ctl']}"
        )
    if not summary["tcp_ok"]:
        errors.append(f"network probe {mode} TCP echo is not PASS")
    if not summary["udp_ok"]:
        errors.append(f"network probe {mode} UDP echo is not PASS")
    return echo, summary


def validate_probe_network_evidence(record: dict[str, Any], errors: list[str]) -> None:
    network = record.get("network", {})
    runs = network.get("probe_runs")
    if not isinstance(runs, dict):
        errors.append("network probe evidence is missing")
        return

    baseline = _validate_stored_run(
        "baseline", runs.get("baseline"), "UNAVAILABLE", errors
    )
    nxless = _validate_stored_run("nxless", runs.get("nxless"), "PASS", errors)
    if baseline is None or nxless is None:
        return

    baseline_echo, baseline_summary = baseline
    nxless_echo, nxless_summary = nxless
    if baseline_echo != nxless_echo:
        errors.append("baseline and NXless network probes must use the same echo target and concurrency")

    expected = nxless_echo
    tcp = network.get("tcp", {})
    udp = network.get("udp", {})
    expected_tcp_target = f"{expected['host']}:{expected['tcp_port']}"
    expected_udp_target = f"{expected['host']}:{expected['udp_port']}"
    if tcp.get("target") != expected_tcp_target:
        errors.append("TCP network target does not match captured NXlessProbe echo target")
    if udp.get("target") != expected_udp_target:
        errors.append("UDP network target does not match captured NXlessProbe echo target")
    if tcp.get("concurrent_sockets") != expected["concurrent"]:
        errors.append("TCP concurrency does not match captured NXlessProbe echo target")
    if udp.get("concurrent_sockets") != expected["concurrent"]:
        errors.append("UDP concurrency does not match captured NXlessProbe echo target")
    if tcp.get("baseline_ok") is not baseline_summary["tcp_ok"]:
        errors.append("TCP baseline verdict does not match captured NXlessProbe summary")
    if udp.get("baseline_ok") is not baseline_summary["udp_ok"]:
        errors.append("UDP baseline verdict does not match captured NXlessProbe summary")
    if tcp.get("nxless_ok") is not nxless_summary["tcp_ok"]:
        errors.append("TCP NXless verdict does not match captured NXlessProbe summary")
    if udp.get("nxless_ok") is not nxless_summary["udp_ok"]:
        errors.append("UDP NXless verdict does not match captured NXlessProbe summary")
