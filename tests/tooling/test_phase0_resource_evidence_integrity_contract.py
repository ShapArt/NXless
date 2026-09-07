import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_hardware.py"
spec = importlib.util.spec_from_file_location("phase0_hardware", SCRIPT)
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)


class Phase0ResourceEvidenceIntegrityContractTests(unittest.TestCase):
    def test_required_resource_evidence_never_depends_on_operator_invented_heap_numbers(self):
        repo = Path(__file__).resolve().parents[2]
        record = phase0.new_record(repo)

        self.assertEqual(record["schema_version"], 4)
        self.assertNotIn("private_heap_bytes", record["resources"])
        self.assertNotIn("peak_heap_bytes", record["resources"])

        cli_source = (repo / "scripts" / "phase0_hw" / "cli.py").read_text(encoding="utf-8")
        self.assertNotIn("--private-heap-bytes", cli_source)
        self.assertNotIn("--peak-heap-bytes", cli_source)

        complete = phase0.synthetic_complete_record()
        complete["resources"].pop("private_heap_bytes", None)
        complete["resources"].pop("peak_heap_bytes", None)
        errors = phase0.validate_record(complete, level="phase0")
        self.assertFalse(any("heap" in error.lower() for error in errors), errors)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
