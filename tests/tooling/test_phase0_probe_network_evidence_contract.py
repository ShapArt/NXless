import importlib
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_hardware.py"
spec = importlib.util.spec_from_file_location("phase0_hardware", SCRIPT)
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)

from phase0_hw import report, schema


class Phase0ProbeNetworkEvidenceContractTests(unittest.TestCase):
    def test_tcp_udp_verdicts_are_bound_to_exact_probe_output(self):
        repo = Path(__file__).resolve().parents[2]
        missing = []

        network = schema.new_record(repo).get("network", {})
        runs = network.get("probe_runs")
        for mode in ("baseline", "nxless"):
            item = runs.get(mode) if isinstance(runs, dict) else None
            if not isinstance(item, dict) or item.get("observed") is not False:
                missing.append(f"schema network.probe_runs.{mode} starts unobserved")

        try:
            probe_evidence = importlib.import_module("phase0_hw.probe_evidence")
        except ModuleNotFoundError:
            probe_evidence = None
            missing.append("probe evidence parser module")

        if probe_evidence is not None:
            try:
                echo = probe_evidence.parse_echo_target_line(
                    "Echo target 192.168.10.25 TCP:5001 UDP:5002 concurrency:4"
                )
                summary = probe_evidence.parse_probe_summary_line(
                    "Summary: ctl=PASS tcp=PASS udp=PASS"
                )
            except (AttributeError, ValueError):
                missing.append("strict probe echo/summary parsers")
            else:
                if echo != {
                    "host": "192.168.10.25",
                    "tcp_port": 5001,
                    "udp_port": 5002,
                    "concurrent": 4,
                }:
                    missing.append("probe echo target values are parsed exactly")
                if summary != {"ctl": "PASS", "tcp_ok": True, "udp_ok": True}:
                    missing.append("probe summary values are parsed exactly")
                for bad in (
                    "Echo target example.com TCP:5001 UDP:5002 concurrency:4",
                    "Summary: tcp=PASS udp=PASS",
                ):
                    parser = (
                        probe_evidence.parse_echo_target_line
                        if bad.startswith("Echo target")
                        else probe_evidence.parse_probe_summary_line
                    )
                    try:
                        parser(bad)
                    except ValueError:
                        pass
                    else:
                        missing.append("malformed probe output is rejected")

        complete = report.synthetic_complete_record()
        complete_runs = complete.get("network", {}).get("probe_runs", {})
        if complete_runs.get("baseline", {}).get("observed") is not True:
            missing.append("synthetic baseline probe output is observed")
        if complete_runs.get("nxless", {}).get("observed") is not True:
            missing.append("synthetic NXless probe output is observed")
        if phase0.validate_record(complete, level="hardware"):
            missing.append("probe-bound synthetic hardware evidence passes")

        no_provenance = phase0.synthetic_complete_record()
        no_provenance.get("network", {}).pop("probe_runs", None)
        errors = phase0.validate_record(no_provenance, level="hardware")
        if not any("probe" in error.lower() and "network" in error.lower() for error in errors):
            missing.append("manual network PASS values without probe output are rejected")

        cli_source = (repo / "scripts" / "phase0_hw" / "cli.py").read_text(encoding="utf-8")
        net_start = cli_source.index('p_net = sub.add_parser("record-network"')
        net_end = cli_source.index('p_app = sub.add_parser("record-app"')
        net_block = cli_source[net_start:net_end]
        for required in ('"--mode"', '"--echo-line"', '"--summary-line"'):
            if required not in net_block:
                missing.append(f"record-network accepts {required}")
        for forbidden in ('"--protocol"', '"--target"', '"--concurrent"', '"--baseline"', '"--nxless"'):
            if forbidden in net_block:
                missing.append(f"record-network does not accept manual {forbidden}")

        command_source = (repo / "scripts" / "phase0_hw" / "record_commands.py").read_text(encoding="utf-8")
        command_start = command_source.index("def _cmd_record_network")
        command_end = command_source.index("def _cmd_record_app")
        command_block = command_source[command_start:command_end]
        if "record_probe_run" not in command_block:
            missing.append("record-network delegates to strict probe evidence recorder")
        for forbidden in ("args.protocol", "args.target", "args.concurrent", "args.baseline", "args.nxless"):
            if forbidden in command_block:
                missing.append(f"record-network does not read manual {forbidden}")

        runbook = (repo / "docs" / "hardware-testing.md").read_text(encoding="utf-8")
        for mode in ("baseline", "nxless"):
            if f"record-network --record evidence/phase0.json --mode {mode}" not in runbook:
                missing.append(f"hardware runbook captures {mode} NXlessProbe output")
        if "record-network --record evidence/phase0.json --protocol" in runbook:
            missing.append("hardware runbook does not use manual protocol PASS recording")

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
