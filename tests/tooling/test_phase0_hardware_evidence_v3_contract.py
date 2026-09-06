import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_hardware.py"
spec = importlib.util.spec_from_file_location("phase0_hardware", SCRIPT)
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)


class Phase0HardwareEvidenceV3ContractTests(unittest.TestCase):
    def test_hardware_record_is_machine_bound_before_original_switch_acceptance(self):
        repo = Path(__file__).resolve().parents[2]
        record = phase0.new_record(repo)
        missing = []

        if record.get("schema_version") != 3:
            missing.append("schema v3")

        build = record.get("build", {})
        for key in ("probe_source_commit", "probe_sha256", "clean_probe_build"):
            if key not in build:
                missing.append(f"build.{key}")

        console = record.get("console", {})
        for key in ("hos", "atmosphere_version", "atmosphere_commit"):
            if console.get(key, None) != "":
                missing.append(f"console.{key} must start unobserved")

        admission = record.get("session_admission", {})
        if admission.get("attempts", None) != []:
            missing.append("session_admission.attempts")

        diagnostics = record.get("diagnostics", {})
        if diagnostics.get("recent_logs_secret_free", "missing") is not None:
            missing.append("diagnostics.recent_logs_secret_free")

        lifecycle = record.get("lifecycle", {})
        for key in ("wifi_ethernet", "ethernet_wifi"):
            if lifecycle.get(key, {}).get("available", "missing") is not None:
                missing.append(f"lifecycle.{key}.available must start unknown")

        source = (repo / "scripts" / "phase0_hw" / "cli.py").read_text(encoding="utf-8")
        for command in (
            "record-probe-build",
            "record-console",
            "record-session-admission",
            "record-diagnostics",
            "record-ethernet-availability",
            "record-failure",
        ):
            if command not in source:
                missing.append(command)

        complete = phase0.synthetic_complete_record()
        if phase0.validate_record(complete, level="phase0"):
            missing.append("synthetic v3 hardware evidence does not pass")

        no_probe = phase0.synthetic_complete_record()
        no_probe["build"]["probe_sha256"] = ""
        if not any("probe" in error.lower() and "sha" in error.lower() for error in phase0.validate_record(no_probe, level="hardware")):
            missing.append("probe SHA validation")

        no_console = phase0.synthetic_complete_record()
        no_console["console"]["hos"] = ""
        if not any("console" in error.lower() and "hos" in error.lower() for error in phase0.validate_record(no_console, level="hardware")):
            missing.append("observed console identity validation")

        no_sessions = phase0.synthetic_complete_record()
        no_sessions["session_admission"]["attempts"] = []
        if not any("session" in error.lower() for error in phase0.validate_record(no_sessions, level="hardware")):
            missing.append("session admission validation")

        secret_logs = phase0.synthetic_complete_record()
        secret_logs["diagnostics"]["recent_logs_secret_free"] = False
        if not any("secret" in error.lower() for error in phase0.validate_record(secret_logs, level="hardware")):
            missing.append("secret-free diagnostics validation")

        excessive = phase0.synthetic_complete_record()
        excessive["network"]["tcp"]["concurrent_sockets"] = 17
        if not any("16" in error for error in phase0.validate_record(excessive, level="hardware")):
            missing.append("probe concurrency upper bound")

        excessive_clients = phase0.synthetic_complete_record()
        excessive_clients["resources"]["peak_clients"] = 65
        if not any("peak_clients" in error and "64" in error for error in phase0.validate_record(excessive_clients, level="hardware")):
            missing.append("registry client high-water upper bound")

        excessive_sockets = phase0.synthetic_complete_record()
        excessive_sockets["resources"]["peak_sockets"] = 513
        if not any("peak_sockets" in error and "512" in error for error in phase0.validate_record(excessive_sockets, level="hardware")):
            missing.append("registry socket high-water upper bound")

        missing_target = phase0.synthetic_complete_record()
        missing_target["network"]["tcp"]["target"] = ""
        if not any("tcp" in error.lower() and "target" in error.lower() for error in phase0.validate_record(missing_target, level="hardware")):
            missing.append("network target validation")

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
