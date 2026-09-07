import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "tools" / "hardware_probe" / "Makefile"


class HardwareProbeMakefileContractTests(unittest.TestCase):
    def test_probe_keeps_werror_but_does_not_promote_libnx_missing_field_warning(self):
        text = MAKEFILE.read_text(encoding="utf-8")
        self.assertIn("-Werror", text)
        self.assertIn("-Wno-error=missing-field-initializers", text)
        self.assertNotIn("-Wno-missing-field-initializers", text)


if __name__ == "__main__":
    unittest.main()
