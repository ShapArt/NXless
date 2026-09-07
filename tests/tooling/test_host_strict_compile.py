import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-host-strict-compile.py"


class HostStrictCompileTests(unittest.TestCase):
    def test_current_production_tree_strict_compiles(self):
        proc = subprocess.run(
            ["python3", str(SCRIPT), "--repo", str(ROOT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("strict production compile: PASS (18 translation units)", proc.stdout)


if __name__ == "__main__":
    unittest.main()
