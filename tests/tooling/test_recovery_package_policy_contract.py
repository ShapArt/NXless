import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "verify-phase0-package.py"
EXACT_WORKFLOW = ROOT / ".github" / "workflows" / "toolchain-probe.yml"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_phase0_package", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RecoveryPackagePolicyContractTests(unittest.TestCase):
    def test_recovery_policy_is_accepted_and_retriggers_exact_build(self):
        verifier = load_verifier()
        violations = []

        with tempfile.TemporaryDirectory() as td:
            package = Path(td) / "package"
            verifier._write_good(package)
            violations.extend(
                error
                for error in verifier.verify(package, ROOT)
                if error.startswith("recovery document missing required concept:")
            )

        workflow = EXACT_WORKFLOW.read_text(encoding="utf-8")
        if "'docs/recovery.md'" not in workflow:
            violations.append(
                "exact Switch workflow does not track docs/recovery.md even though package verification depends on it"
            )

        self.assertEqual([], violations, "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
