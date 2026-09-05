import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "sysmodule" / "Makefile"
WORKFLOW = ROOT / ".github" / "workflows" / "toolchain-probe.yml"


class SwitchBuildMakefileContractTests(unittest.TestCase):
    def test_clean_source_build_explicitly_builds_pinned_libstratosphere(self):
        text = MAKEFILE.read_text(encoding="utf-8")
        self.assertIn("ATMOSPHERE_LIBSTRATOSPHERE", text)
        self.assertIn("$(ATMOSPHERE_LIBRARIES_DIR)/libstratosphere", text)
        self.assertIn("nx_release", text)
        self.assertIn("$(ATMOSPHERE_LIBSTRATOSPHERE):", text)

    def test_nxless_objects_depend_on_the_explicit_libstratosphere_target(self):
        text = MAKEFILE.read_text(encoding="utf-8")
        self.assertIn("$(OFILES): $(ATMOSPHERE_LIBSTRATOSPHERE)", text)
        self.assertNotIn("$(OFILES): $(ATMOSPHERE_LIBRARIES_DIR)/libstratosphere/$(ATMOSPHERE_LIBRARY_DIR)/libstratosphere.a", text)

    def test_container_build_marks_the_checkout_as_git_safe(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('git config --global --add safe.directory "$PWD"', text)


if __name__ == "__main__":
    unittest.main()
