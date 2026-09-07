import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_hardware.py"
spec = importlib.util.spec_from_file_location("phase0_hardware", SCRIPT)
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)

from phase0_hw import record_commands


class Phase0RegistryTelemetryContractTests(unittest.TestCase):
    def test_registry_high_water_is_bound_to_observed_control_telemetry(self):
        repo = Path(__file__).resolve().parents[2]
        missing = []

        resources = phase0.new_record(repo).get("resources", {})
        telemetry = resources.get("registry_telemetry")
        if telemetry != {
            "observed": False,
            "status_line": "",
            "active_clients": None,
            "client_high_water": None,
            "active_sockets": None,
            "socket_high_water": None,
            "dropped_logs": None,
            "last_error": None,
        }:
            missing.append("resources.registry_telemetry starts unobserved")

        parser = getattr(record_commands, "parse_registry_status_line", None)
        if parser is None:
            missing.append("strict nxl:ctl registry status parser")
        else:
            parsed = parser(
                "clients=0 client-high-water=4 sockets=0 socket-high-water=16 "
                "dropped-logs=2 last-error=-5"
            )
            expected = {
                "active_clients": 0,
                "client_high_water": 4,
                "active_sockets": 0,
                "socket_high_water": 16,
                "dropped_logs": 2,
                "last_error": -5,
            }
            if parsed != expected:
                missing.append("nxl:ctl registry status values are parsed exactly")
            try:
                parser("client-high-water=4 socket-high-water=16")
            except ValueError:
                pass
            else:
                missing.append("malformed nxl:ctl status is rejected")

        cli_source = (repo / "scripts" / "phase0_hw" / "cli.py").read_text(encoding="utf-8")
        if "record-registry-telemetry" not in cli_source:
            missing.append("record-registry-telemetry CLI command")

        complete = phase0.synthetic_complete_record()
        complete_telemetry = complete.get("resources", {}).get("registry_telemetry", {})
        if complete_telemetry.get("observed") is not True:
            missing.append("synthetic complete evidence contains observed registry telemetry")
        if phase0.validate_record(complete, level="hardware"):
            missing.append("synthetic telemetry-bound hardware evidence does not pass")

        manual = phase0.synthetic_complete_record()
        manual.get("resources", {}).pop("registry_telemetry", None)
        errors = phase0.validate_record(manual, level="hardware")
        if not any("registry telemetry" in error.lower() for error in errors):
            missing.append("manual registry peaks without telemetry are rejected")

        mismatch = phase0.synthetic_complete_record()
        mismatch_resources = mismatch.get("resources", {})
        mismatch_resources["peak_clients"] = int(mismatch_resources.get("peak_clients", 0)) + 1
        errors = phase0.validate_record(mismatch, level="hardware")
        if not any("peak_clients" in error and "telemetry" in error.lower() for error in errors):
            missing.append("manual client peak cannot disagree with telemetry")

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
