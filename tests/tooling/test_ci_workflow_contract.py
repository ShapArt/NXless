import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "phase0-ci.yml"
CI_LOCK = ROOT / "third_party" / "locks" / "ci.lock"
CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
CMAKE_SHA256 = "d6c83076c575bc00b823522ac974bda66d0af05d6ddc30e739c12385cf32c6cc"
UPLOAD_ARTIFACT_SHA = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"


class Phase0CiWorkflowContractTests(unittest.TestCase):
    def _text(self) -> str:
        self.assertTrue(WORKFLOW.is_file(), f"missing workflow: {WORKFLOW}")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_supply_chain_and_permissions_are_pinned(self):
        text = self._text()
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("pull_request_target:", text)
        self.assertIn(f"actions/checkout@{CHECKOUT_SHA}", text)
        uses = re.findall(r"^\s*-?\s*uses:\s*([^\s#]+)", text, flags=re.MULTILINE)
        self.assertGreaterEqual(len(uses), 1)
        for ref in uses:
            self.assertRegex(ref, r"@[0-9a-f]{40}$", f"action is not pinned to a full commit SHA: {ref}")

    def test_offline_job_runs_all_portable_phase0_gates(self):
        text = self._text()
        required = (
            "make hardware-tool-test",
            "make host-test-offline",
            "python3 scripts/verify-host-strict-compile.py --repo .",
            "make verify-package-policy",
            "make verify-locks",
            "make check-title-id",
            "git diff --check",
        )
        for command in required:
            self.assertIn(command, text)

    def test_canonical_job_uses_verified_cmake_4_4_3_and_catch2_path(self):
        text = self._text()
        self.assertIn("cmake-4.4.3-linux-x86_64.tar.gz", text)
        self.assertIn(CMAKE_SHA256, text)
        self.assertIn("cmake --version", text)
        self.assertIn("make host-test", text)

    def test_ci_artifacts_are_locked_outside_the_workflow(self):
        self.assertTrue(CI_LOCK.is_file(), f"missing CI dependency lock: {CI_LOCK}")
        lock = {}
        for raw in CI_LOCK.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            lock[key] = value
        self.assertEqual(lock.get("actions_checkout.version"), "7.0.1")
        self.assertEqual(lock.get("actions_checkout.commit"), CHECKOUT_SHA)
        self.assertEqual(lock.get("actions_upload_artifact.version"), "7.0.1")
        self.assertEqual(lock.get("actions_upload_artifact.commit"), UPLOAD_ARTIFACT_SHA)
        self.assertEqual(lock.get("cmake.version"), "4.4.3")
        self.assertEqual(lock.get("cmake.linux_x86_64_sha256"), CMAKE_SHA256)
        text = self._text()
        self.assertIn(lock["actions_checkout.commit"], text)
        self.assertIn(lock["actions_upload_artifact.commit"], text)
        self.assertIn(lock["cmake.linux_x86_64_sha256"], text)

    def test_ci_lock_is_enforced_by_dependency_verifier(self):
        result = subprocess.run(
            [sys.executable, "scripts/verify-dependency-lock.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ci: actions/checkout=7.0.1", result.stdout)
        self.assertIn("upload-artifact=7.0.1", result.stdout)
        self.assertIn("cmake=4.4.3", result.stdout)

    def test_evidence_job_exports_machine_readable_preflight(self):
        text = self._text()
        self.assertIn("evidence:", text)
        self.assertIn("needs: [portable-gates, canonical-host]", text)
        self.assertIn("make hardware-new-record", text)
        self.assertIn("make hardware-record-host", text)
        self.assertIn("--level preflight", text)
        self.assertIn("--markdown", text)
        self.assertIn(f"actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}", text)
        self.assertIn("if-no-files-found: error", text)
        self.assertIn("retention-days: 30", text)
        self.assertIn("id: record-evidence", text)
        self.assertIn('source_sha="$(git rev-parse HEAD)"', text)
        self.assertIn("source_sha=$source_sha", text)
        self.assertIn("phase0-preflight-${{ steps.record-evidence.outputs.source_sha }}", text)
        self.assertIn("evidence/phase0-${{ steps.record-evidence.outputs.source_sha }}.json", text)
        self.assertIn("evidence/phase0-${{ steps.record-evidence.outputs.source_sha }}.md", text)

    def test_workflow_does_not_claim_switch_build(self):
        text = self._text().lower()
        self.assertNotIn("make switch", text)
        self.assertNotIn("switch-package", text)
        self.assertNotIn("devkita64", text)
        self.assertNotRegex(text, r"\b(switch|horizon)[-_ ]?(build|package)\b")


if __name__ == "__main__":
    unittest.main()
