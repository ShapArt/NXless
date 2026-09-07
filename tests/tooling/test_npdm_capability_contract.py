import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NPDM = ROOT / "sysmodule" / "config" / "exefs.nsp.json"


class NpdmCapabilityContractTests(unittest.TestCase):
    def test_phase0_filesystem_permission_is_sdcard_only(self):
        data = json.loads(NPDM.read_text(encoding="utf-8"))
        self.assertEqual(data["filesystem_access"]["permissions"], "0x0000000000200000")

    def test_phase0_service_acl_is_exact_and_has_no_wildcards(self):
        data = json.loads(NPDM.read_text(encoding="utf-8"))
        self.assertEqual(data["service_access"], ["fsp-srv", "bsd:u"])
        self.assertEqual(data["service_host"], ["nxl:ctl", "bsd:u"])
        self.assertFalse(any("*" in name for name in data["service_access"] + data["service_host"]))


if __name__ == "__main__":
    unittest.main()
