import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_hardware.py"
spec = importlib.util.spec_from_file_location("phase0_hardware", SCRIPT)
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)


class Phase0HomeResumeRepetitionContractTests(unittest.TestCase):
    def test_home_resume_is_repeated_not_single_shot(self):
        self.assertGreaterEqual(phase0.REQUIRED_COUNTS.get("home_resume", 0), 2)

        record = phase0.synthetic_complete_record()
        required = phase0.REQUIRED_COUNTS["home_resume"]
        self.assertGreaterEqual(record["lifecycle"]["home_resume"]["attempts"], required)
        self.assertEqual(phase0.validate_record(record, level="hardware"), [])

        single = phase0.synthetic_complete_record()
        single["lifecycle"]["home_resume"] = {"attempts": 1, "passes": 1}
        errors = phase0.validate_record(single, level="hardware")
        self.assertTrue(any("HOME/resume" in error and str(required) in error for error in errors))

        runbook = (Path(__file__).resolve().parents[2] / "docs" / "hardware-testing.md").read_text(encoding="utf-8")
        self.assertIn("HOME/resume x2", runbook)


if __name__ == "__main__":
    unittest.main()
