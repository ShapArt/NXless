import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_hardware.py"
spec = importlib.util.spec_from_file_location("phase0_hardware", SCRIPT)
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)

from phase0_hw import report, schema


class Phase0RegistrySingleSourceContractTests(unittest.TestCase):
    def test_registry_peaks_have_one_operator_evidence_source(self):
        repo = Path(__file__).resolve().parents[2]
        missing = []

        telemetry = schema.new_record(repo).get("resources", {}).get("registry_telemetry")
        if not isinstance(telemetry, dict) or telemetry.get("observed") is not False:
            missing.append("schema.new_record owns unobserved registry telemetry shape")

        complete = report.synthetic_complete_record()
        complete_telemetry = complete.get("resources", {}).get("registry_telemetry", {})
        if complete_telemetry.get("observed") is not True:
            missing.append("report.synthetic_complete_record owns observed registry telemetry")
        if phase0.validate_record(complete, level="hardware"):
            missing.append("direct report synthetic evidence passes hardware validation")

        cli_source = (repo / "scripts" / "phase0_hw" / "cli.py").read_text(encoding="utf-8")
        for option in ("--peak-clients", "--peak-sockets"):
            if option in cli_source:
                missing.append(f"record-resources does not accept {option}")

        command_source = (repo / "scripts" / "phase0_hw" / "record_commands.py").read_text(encoding="utf-8")
        for attribute in ("args.peak_clients", "args.peak_sockets"):
            if attribute in command_source:
                missing.append(f"record-resources does not read {attribute}")

        runbook = (repo / "docs" / "hardware-testing.md").read_text(encoding="utf-8")
        if "record-registry-telemetry" not in runbook:
            missing.append("hardware runbook records nxl:ctl registry telemetry")
        for option in ("--peak-clients", "--peak-sockets"):
            if option in runbook:
                missing.append(f"hardware runbook does not ask operator for {option}")

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
