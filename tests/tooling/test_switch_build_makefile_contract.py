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

    def test_outer_build_uses_a_phony_action_not_the_build_directory_as_the_target(self):
        text = MAKEFILE.read_text(encoding="utf-8")
        self.assertIn(".PHONY: all clean dist verify-source nxless-build", text)
        self.assertIn("all: verify-source $(ATMOSPHERE_LIBSTRATOSPHERE) nxless-build", text)
        self.assertIn("nxless-build: $(ATMOSPHERE_LIBSTRATOSPHERE)", text)
        self.assertIn("-C $(SYSMODULE_DIR)/$(BUILD) -f $(THIS_MAKEFILE)", text)
        self.assertIn("test -f $(TARGET).nsp", text)
        self.assertNotIn("all: verify-source $(ATMOSPHERE_LIBSTRATOSPHERE) $(BUILD)", text)
        self.assertNotIn("$(BUILD): $(ATMOSPHERE_LIBSTRATOSPHERE)", text)

    def test_recursive_build_explicitly_selects_inner_all_target(self):
        text = MAKEFILE.read_text(encoding="utf-8")
        self.assertIn(
            "-C $(SYSMODULE_DIR)/$(BUILD) -f $(THIS_MAKEFILE) NXLESS_ATMOSPHERE_ROOT=$(NXLESS_ATMOSPHERE_ROOT) all",
            text,
        )

    def test_dist_writes_release_zip_to_repository_output_directory(self):
        text = MAKEFILE.read_text(encoding="utf-8")
        self.assertIn("PACKAGE_ZIP := $(REPO_ROOT)/output/NXless-phase0.zip", text)
        self.assertIn("zip -q -r $(PACKAGE_ZIP) .", text)
        self.assertNotIn("../../NXless-phase0.zip", text)

    def test_container_build_marks_the_checkout_as_git_safe(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('git config --global --add safe.directory "$PWD"', text)


if __name__ == "__main__":
    unittest.main()
