import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from phase0_hw import gate_common


class Phase0GateTimeoutContractTests(unittest.TestCase):
    def test_gate_runner_has_finite_default_timeout(self):
        self.assertEqual(gate_common.DEFAULT_GATE_TIMEOUT_SECONDS, 300)

        completed = Mock(returncode=0, stdout="ok\n", stderr="")
        with patch.object(gate_common.subprocess, "run", return_value=completed) as run:
            status, output = gate_common._run_gate(["example-gate"])

        self.assertEqual(status, "pass")
        self.assertEqual(output, "ok")
        self.assertEqual(run.call_args.kwargs.get("timeout"), 300)

    def test_timeout_is_a_hard_failure_with_partial_diagnostics(self):
        timeout = subprocess.TimeoutExpired(
            cmd=["make", "host-test"],
            timeout=7,
            output=b"partial stdout\n",
            stderr=b"partial stderr\n",
        )
        with patch.object(gate_common.subprocess, "run", side_effect=timeout):
            status, output = gate_common._run_gate(
                ["make", "host-test"], timeout_seconds=7
            )

        self.assertEqual(status, "fail")
        self.assertIn("gate timed out after 7s", output)
        self.assertIn("make host-test", output)
        self.assertIn("partial stdout", output)
        self.assertIn("partial stderr", output)
        self.assertNotEqual(gate_common._canonical_host_state(status, output)[0], "blocked")

    def test_explicit_timeout_is_forwarded_to_subprocess(self):
        completed = Mock(returncode=2, stdout="", stderr="failed")
        with patch.object(gate_common.subprocess, "run", return_value=completed) as run:
            status, output = gate_common._run_gate(
                ["custom-gate", "--check"], timeout_seconds=11
            )

        self.assertEqual(status, "fail")
        self.assertEqual(output, "failed")
        self.assertEqual(run.call_args.kwargs.get("timeout"), 11)


if __name__ == "__main__":
    unittest.main()
