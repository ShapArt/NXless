import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "sysmodule" / "Makefile"


class NpdmBuildContractTests(unittest.TestCase):
    def test_app_json_is_defined_before_atmosphere_template_include(self):
        lines = MAKEFILE.read_text(encoding="utf-8").splitlines()

        app_json_line = next(
            i
            for i, line in enumerate(lines)
            if line.lstrip().startswith("APP_JSON") and ":=" in line
        )
        stratosphere_include_line = next(
            i
            for i, line in enumerate(lines)
            if line.strip() == "include $(STRATOSPHERE_MK)"
        )

        self.assertLess(
            app_json_line,
            stratosphere_include_line,
            "APP_JSON must exist before stratosphere.mk parses libnx switch_rules; "
            "otherwise the built-in %.npdm rule invokes npdmtool without its JSON input",
        )


if __name__ == "__main__":
    unittest.main()
