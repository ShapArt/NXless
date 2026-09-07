import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "sysmodule" / "include" / "nxless" / "sys" / "ipc" / "control_service.hpp"


class ControlServiceHeaderContractTests(unittest.TestCase):
    def test_header_owns_hos_version_dependency(self):
        text = HEADER.read_text(encoding="utf-8")
        self.assertIn(
            "#include <nxless/sys/platform/compatibility.hpp>",
            text,
            "control_service.hpp exposes platform::HosVersion and must include its defining header directly",
        )


if __name__ == "__main__":
    unittest.main()
