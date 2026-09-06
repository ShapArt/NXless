import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "toolchain-probe.yml"
PINNED_IMAGE = "devkitpro/devkita64:20260219@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282"
PACKAGE_SHA256 = (
    "0d61ad4946eb1080c6e645c41f0cfaac0a2eba5fec88426fef8f03363e933b5a",
    "8192b899f0a5fcfe10d11fa63a631b45310c0c8f0b98d88c7c283c16e9d6b0fa",
    "fc97ba1009a94b68f8714c3cc548ef697ca82687b72fe0c05a7ca3df81beb53e",
    "66f100490dafe506495ee083bc932aa2c2f231b5dafaa2b203d1832389b700e9",
    "c6950bdf8e4b872ece492225368c03e633776329548a7494f91aa1e8f239cd8a",
)
ATMOSPHERE_COMMIT = "5388824be146a89619e8d641acd64599cf1c5f62"


class ToolchainProbeWorkflowContractTests(unittest.TestCase):
    def _text(self) -> str:
        self.assertTrue(WORKFLOW.is_file(), f"missing workflow: {WORKFLOW}")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_probe_uses_pinned_official_bootstrap_image(self):
        text = self._text()
        self.assertIn("workflow_dispatch:", text)
        self.assertIn(f"image: {PINNED_IMAGE}", text)
        self.assertIn("permissions:\n  contents: read", text)

    def test_probe_runs_for_switch_build_critical_changes(self):
        text = self._text()
        required_paths = (
            "'.github/workflows/toolchain-probe.yml'",
            "'sysmodule/**'",
            "'common/**'",
            "'config/**'",
            "'third_party/locks/switch-toolchain.lock'",
            "'scripts/verify-switch-toolchain.sh'",
            "'scripts/verify-atmosphere-source.sh'",
            "'scripts/verify-phase0-package.py'",
        )
        for path in required_paths:
            self.assertIn(f"      - {path}", text)

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
        for digest in PACKAGE_SHA256:
            self.assertIn(digest, text)

    def test_probe_never_passes_detached_signatures_to_pacman_u(self):
        text = self._text()
        self.assertGreaterEqual(text.count("-name '*.pkg.tar.zst'"), 2)
        self.assertNotIn("-name '*.pkg.tar.*'", text)

    def test_probe_fetches_exact_atmosphere_and_produces_switch_package(self):
        text = self._text()
        self.assertIn("tag 1.11.2", text)
        self.assertIn(ATMOSPHERE_COMMIT, text)
        self.assertIn("scripts/verify-atmosphere-source.sh", text)
        self.assertIn("output/NXless-phase0.zip", text)

    def test_probe_uses_clean_canonical_phase0_acceptance_pipeline(self):
        text = self._text()
        required_paths = (
            "'Makefile'",
            "'.gitignore'",
            "'scripts/phase0_build.py'",
            "'scripts/phase0_hardware.py'",
            "'scripts/phase0_hw/**'",
            "'tests/tooling/**'",
            "'tools/hardware_probe/**'",
        )
        for path in required_paths:
            self.assertIn(f"      - {path}", text)

        required_markers = (
            ".cache/toolchain",
            ".cache/toolchain-package-sha256.expected",
            "evidence/toolchain-package-sha256.txt",
            "make phase0-build",
            'RECORD="evidence/phase0-exact-${GITHUB_SHA}.json"',
            "evidence/phase0-package-sha256.txt",
            "evidence/phase0-exact-${{ github.sha }}.json",
            "if-no-files-found: error",
        )
        for marker in required_markers:
            self.assertIn(marker, text)

        self.assertNotIn("make switch-package", text)
        self.assertNotIn("mkdir -p toolchain-cache", text)
        self.assertNotIn("cat > toolchain-package-sha256.expected", text)

    def test_probe_archives_test_only_hardware_probe_after_clean_acceptance(self):
        text = self._text()
        required_markers = (
            "Build test-only hardware probe",
            "make -C tools/hardware_probe clean",
            "make -C tools/hardware_probe",
            "test -f tools/hardware_probe/NXlessProbe.nro",
            "sha256sum tools/hardware_probe/NXlessProbe.nro | tee evidence/phase0-probe-sha256.txt",
            "evidence/phase0-probe-sha256.txt",
            "tools/hardware_probe/NXlessProbe.nro",
        )
        for marker in required_markers:
            self.assertIn(marker, text)

        self.assertLess(
            text.index("make phase0-build"),
            text.index("make -C tools/hardware_probe clean"),
            "test-only probe must be built only after the clean canonical Phase 0 acceptance build",
        )


if __name__ == "__main__":
    unittest.main()
