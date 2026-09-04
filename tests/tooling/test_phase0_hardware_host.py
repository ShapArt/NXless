import importlib.util
import json
import socket
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_hardware.py"
spec = importlib.util.spec_from_file_location("phase0_hardware", SCRIPT)
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)


class Phase0HardwareTests(unittest.TestCase):
    def test_preflight_reports_canonical_blocker_without_cascading_fault_noise(self):
        from unittest.mock import patch
        record = phase0.new_record(Path(__file__).resolve().parents[2])
        gate_results = [
            ("fail", "fatal: unable to access https://github.com/catchorg/Catch2.git: Could not resolve host: github.com"),
            ("pass", "offline-shim tests: 49 total, 0 failed"),
            ("pass", "strict compile pass"),
            ("pass", "package policy pass"),
            ("pass", "dependency locks pass"),
            ("pass", "title id pass"),
            ("pass", "diff check pass"),
        ]
        with patch.object(phase0, "_run_gate", side_effect=gate_results):
            updated, _ = phase0.collect_host_verification(record, Path("/repo"))
        errors = phase0.validate_record(updated, level="preflight")
        self.assertTrue(any("canonical make host-test is BLOCKED" in e for e in errors))
        self.assertFalse(any("fault_injection." in e for e in errors))
        self.assertFalse(any("offline sanitizer" in e for e in errors))

    def test_preflight_reports_offline_sanitizer_failure_when_canonical_is_blocked(self):
        record = phase0.synthetic_complete_record()
        hv = record["host_verification"]
        hv["canonical_host_test"] = "blocked"
        hv["canonical_block_reason"] = "fatal: Could not resolve host: github.com"
        hv["offline_sanitizer"] = "fail"
        errors = phase0.validate_record(record, level="preflight")
        self.assertTrue(any("canonical make host-test is BLOCKED" in e for e in errors))
        self.assertIn("offline sanitizer host suite is not PASS", errors)

    def test_preflight_reports_missing_switch_inputs(self):
        from unittest.mock import patch
        with patch.dict("os.environ", {"DEVKITPRO": "", "NXLESS_ATMOSPHERE_ROOT": ""}, clear=False):
            result = phase0.preflight(Path(__file__).resolve().parents[2])
        self.assertFalse(result["ready"])
        self.assertIn("DEVKITPRO is not set", result["blockers"])
        self.assertIn("NXLESS_ATMOSPHERE_ROOT is not set", result["blockers"])
        self.assertEqual(result["toolchain_gate"], "blocked")
        self.assertEqual(result["atmosphere_gate"], "blocked")

    def test_record_helpers_increment_without_hiding_failures(self):
        record = phase0.new_record(Path(__file__).resolve().parents[2])
        phase0.append_boot(record, "disable", cold_boot=True, home_reached=True, networking=True, ctl_status="DisabledByFlag")
        phase0.append_boot(record, "mitm", cold_boot=True, home_reached=True, networking=True, ctl_status="Transparent")
        phase0.add_lifecycle_attempt(record, "sleep_wake", passed=True)
        phase0.add_lifecycle_attempt(record, "sleep_wake", passed=False)
        self.assertEqual(len(record["recovery"]["disable_flag_boots"]), 1)
        self.assertEqual(len(record["transparent_mitm"]["cold_boots"]), 1)
        self.assertEqual(record["lifecycle"]["sleep_wake"], {"attempts": 2, "passes": 1})

    def test_new_record_rejects_user_supplied_package_argument(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "record.json"
            proc = subprocess.run(
                ["python3", str(SCRIPT), "new-record", "--repo", str(Path(__file__).resolve().parents[2]), "--package", "arbitrary.zip", "--output", str(output)],
                capture_output=True, text=True, check=False,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unrecognized arguments: --package", proc.stderr)

    def test_cli_exposes_machine_observed_host_and_build_recorders(self):
        import subprocess
        proc = subprocess.run(["python3", str(SCRIPT), "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("record-host", proc.stdout)
        self.assertIn("record-build", proc.stdout)

    def test_collect_host_verification_records_machine_observed_gates(self):
        from unittest.mock import patch
        record = phase0.synthetic_complete_record()
        record["host_verification"] = phase0.new_record(Path(__file__).resolve().parents[2])["host_verification"]
        gate_results = [
            ("pass", "ctest: all pass"),
            ("pass", "strict compile pass"),
            ("pass", "package policy pass"),
            ("pass", "dependency locks pass"),
            ("pass", "title id pass"),
            ("pass", "diff check pass"),
        ]
        with patch.object(phase0, "_run_gate", side_effect=gate_results):
            updated, blockers = phase0.collect_host_verification(record, Path("/repo"))
        self.assertEqual(blockers, [])
        hv = updated["host_verification"]
        self.assertEqual(hv["canonical_host_test"], "pass")
        self.assertEqual(hv["offline_sanitizer"], "pass")
        self.assertEqual(hv["asan"], "none")
        self.assertEqual(hv["ubsan"], "none")
        self.assertTrue(hv["strict_compile"])
        self.assertTrue(hv["package_verifier"])
        self.assertTrue(hv["dependency_lock_verifier"])
        self.assertTrue(hv["title_id_collision_gate"])
        self.assertTrue(hv["git_diff_check"])
        self.assertTrue(all(hv["fault_injection"].values()))

    def test_collect_host_verification_classifies_github_dns_as_blocked_but_records_offline_sanitizer(self):
        from unittest.mock import patch
        record = phase0.new_record(Path(__file__).resolve().parents[2])
        gate_results = [
            ("fail", "fatal: unable to access https://github.com/catchorg/Catch2.git: Could not resolve host: github.com"),
            ("pass", "offline-shim tests: 49 total, 0 failed"),
            ("pass", "strict compile pass"),
            ("pass", "package policy pass"),
            ("pass", "dependency locks pass"),
            ("pass", "title id pass"),
            ("pass", "diff check pass"),
        ]
        with patch.object(phase0, "_run_gate", side_effect=gate_results):
            updated, blockers = phase0.collect_host_verification(record, Path("/repo"))
        hv = updated["host_verification"]
        self.assertEqual(hv["canonical_host_test"], "blocked")
        self.assertIn("Could not resolve host", hv["canonical_block_reason"])
        self.assertEqual(hv["offline_sanitizer"], "pass")
        self.assertEqual(hv["asan"], "none")
        self.assertEqual(hv["ubsan"], "none")
        self.assertTrue(all(hv["fault_injection"].values()))
        self.assertTrue(any("canonical host test blocked" in b for b in blockers))


if __name__ == "__main__":
    unittest.main()
