import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "toolchain-probe.yml"
PINNED_IMAGE = "devkitpro/devkita64:20260219@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282"


class ToolchainProbeWorkflowContractTests(unittest.TestCase):
    def _text(self) -> str:
        self.assertTrue(WORKFLOW.is_file(), f"missing workflow: {WORKFLOW}")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_probe_is_isolated_and_uses_pinned_official_bootstrap_image(self):
        text = self._text()
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("paths:\n      - '.github/workflows/toolchain-probe.yml'", text)
        self.assertIn(f"image: {PINNED_IMAGE}", text)
        self.assertIn("permissions:\n  contents: read", text)

    def test_probe_never_performs_a_rolling_system_upgrade(self):
        text = self._text()
        self.assertNotIn("pacman -Syu", text)
        self.assertNotIn("dkp-pacman -Syu", text)
        self.assertNotIn("--sysupgrade", text)

    def test_probe_requests_exact_phase0_toolchain_versions(self):
        text = self._text()
        required = (
            "devkitA64=r30-1",
            "devkita64-binutils=2.46.0-1",
            "devkita64-gcc=16.1.0-1",
            "devkita64-newlib=4.6.0.20260123-4",
            "libnx=4.12.0-1",
            "scripts/verify-switch-toolchain.sh",
        )
        for value in required:
            self.assertIn(value, text)

    def test_probe_records_downloaded_package_hashes_before_install(self):
        text = self._text()
        self.assertIn("--downloadonly", text)
        self.assertIn("sha256sum", text)
        self.assertIn("toolchain-package-sha256.txt", text)

    def test_probe_never_passes_detached_signatures_to_pacman_u(self):
        text = self._text()
        self.assertGreaterEqual(text.count("-name '*.pkg.tar.zst'"), 2)
        self.assertNotIn("-name '*.pkg.tar.*'", text)


if __name__ == "__main__":
    unittest.main()
