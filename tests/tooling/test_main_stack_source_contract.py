import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "sysmodule" / "source" / "main.cpp"
NPDM = ROOT / "sysmodule" / "config" / "exefs.nsp.json"
CONFIG = ROOT / "common" / "include" / "nxless" / "config" / "config.hpp"


class MainStackSourceContractTests(unittest.TestCase):
    def test_config_workspace_is_not_allocated_on_main_stack(self):
        main = MAIN.read_text(encoding="utf-8")
        npdm = json.loads(NPDM.read_text(encoding="utf-8"))
        config = CONFIG.read_text(encoding="utf-8")

        main_stack = int(npdm["main_thread_stack_size"], 0)
        match = re.search(r"kMaxConfigBytes\s*=\s*(\d+)\s*\*\s*(\d+)", config)
        self.assertIsNotNone(match)
        workspace = int(match.group(1)) * int(match.group(2))
        self.assertGreaterEqual(workspace, main_stack)

        self.assertNotIn("nxless::sys::config::SdConfigStore store;", main)
        self.assertIn("nxless::sys::config::SdConfigStore& GetSdConfigStore()", main)
        self.assertIn("GetSdConfigStore().Load(&g_sd_fs)", main)

    def test_sd_handles_are_released_after_boot_config_load(self):
        main = MAIN.read_text(encoding="utf-8")
        load = main.index("GetSdConfigStore().Load(&g_sd_fs)")
        close = main.index("fsFsClose(&g_sd_fs);", load)
        fs_exit = main.index("fsExit();", close)
        query_hos = main.index("QueryHosVersion()", fs_exit)

        self.assertLess(load, close)
        self.assertLess(close, fs_exit)
        self.assertLess(fs_exit, query_hos)


if __name__ == "__main__":
    unittest.main()
