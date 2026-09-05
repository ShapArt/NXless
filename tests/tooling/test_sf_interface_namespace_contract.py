import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEADERS = (
    ROOT / "sysmodule" / "include" / "nxless" / "sys" / "ipc" / "control_service.hpp",
    ROOT / "sysmodule" / "include" / "nxless" / "sys" / "bsd" / "bsd_mitm_service.hpp",
)


class SfInterfaceNamespaceContractTests(unittest.TestCase):
    def test_nxless_sf_namespaces_expose_pinned_atmosphere_hos_namespace(self):
        for header in HEADERS:
            with self.subTest(header=header.relative_to(ROOT)):
                text = header.read_text(encoding="utf-8")
                self.assertIn(
                    "namespace hos = ::ams::hos;",
                    text,
                    "Atmosphere SF method metadata expands hos::Version_Min/Max inside the target namespace",
                )


if __name__ == "__main__":
    unittest.main()
