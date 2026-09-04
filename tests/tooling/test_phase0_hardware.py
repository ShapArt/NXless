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
    def test_new_record_is_pinned_and_incomplete(self):
        record = phase0.new_record(Path(__file__).resolve().parents[2])
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["build"]["atmosphere_commit"], "5388824")
        self.assertEqual(record["build"]["libnx_commit"], "7644c9b26099aa2d2145bc72a21ee24190e92085")
        self.assertEqual(record["build"]["libnx_version"], "4.12.0")
        self.assertEqual(record["build"]["devkitA64"], "r30")
        self.assertEqual(record["build"]["hos"], "22.5.0")
        self.assertIn("source_tree_clean", record["build"])
        errors = phase0.validate_record(record, level="phase0")
        self.assertTrue(any("disable.flag cold boots" in e for e in errors))
        self.assertTrue(any("transparent MITM cold boots" in e for e in errors))

    def test_dirty_source_tree_blocks_phase0_verdict(self):
        record = phase0.synthetic_complete_record()
        record["build"]["source_tree_clean"] = False
        errors = phase0.validate_record(record, level="phase0")
        self.assertIn("source tree was dirty when evidence record was created", errors)

    def test_invalid_build_identity_is_rejected(self):
        record = phase0.synthetic_complete_record()
        record["build"]["nxless_commit"] = "short"
        record["build"]["package_sha256"] = "xyz"
        errors = phase0.validate_record(record, level="phase0")
        self.assertIn("build.nxless_commit must be a full 40-hex git commit", errors)
        self.assertIn("build.package_sha256 must be 64 lowercase hex characters", errors)

    def test_duplicate_apps_do_not_satisfy_two_app_gate(self):
        record = phase0.synthetic_complete_record()
        record["applications"] = [record["applications"][0], dict(record["applications"][0])]
        errors = phase0.validate_record(record, level="phase0")
        self.assertIn("at least two distinct real network applications/games must match baseline", errors)

    def test_negative_resource_values_are_rejected(self):
        record = phase0.synthetic_complete_record()
        record["resources"]["peak_sockets"] = -1
        errors = phase0.validate_record(record, level="phase0")
        self.assertIn("resources.peak_sockets must be non-negative", errors)

    def test_runtime_status_names_are_exact(self):
        record = phase0.synthetic_complete_record()
        record["recovery"]["disable_flag_boots"][0]["ctl_status"] = "DisabledByFlag"
        record["transparent_mitm"]["cold_boots"][0]["ctl_status"] = "Transparent"
        errors = phase0.validate_record(record, level="phase0")
        self.assertTrue(any("SafeDisabled" in e for e in errors))
        self.assertTrue(any("DisconnectedPassthrough" in e for e in errors))

    def test_complete_synthetic_record_passes(self):
        record = phase0.synthetic_complete_record()
        self.assertEqual(phase0.validate_record(record, level="phase0"), [])

    def test_failed_boot_is_not_hidden_by_count(self):
        record = phase0.synthetic_complete_record()
        record["recovery"]["disable_flag_boots"][4]["home_reached"] = False
        errors = phase0.validate_record(record, level="phase0")
        self.assertTrue(any("disable.flag boot attempt 5" in e for e in errors))

    def test_insufficient_lifecycle_counts_fail(self):
        record = phase0.synthetic_complete_record()
        record["lifecycle"]["sleep_wake"] = {"attempts": 19, "passes": 19}
        errors = phase0.validate_record(record, level="phase0")
        self.assertTrue(any("sleep/wake requires 20" in e for e in errors))

    def test_markdown_summary_contains_verdict(self):
        record = phase0.synthetic_complete_record()
        text = phase0.render_markdown(record, level="phase0")
        self.assertIn("Phase 0 verdict: PASS", text)
        self.assertIn(record["build"]["nxless_commit"], text)

    def test_markdown_verdict_label_matches_validation_level(self):
        record = phase0.synthetic_complete_record()
        preflight = phase0.render_markdown(record, level="preflight")
        hardware = phase0.render_markdown(record, level="hardware")
        phase0_text = phase0.render_markdown(record, level="phase0")
        self.assertIn("Preflight verdict: PASS", preflight)
        self.assertNotIn("Phase 0 verdict:", preflight)
        self.assertIn("Hardware verdict: PASS", hardware)
        self.assertIn("Phase 0 verdict: PASS", phase0_text)


if __name__ == "__main__":
    unittest.main()
