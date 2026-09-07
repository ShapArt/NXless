import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class HorizonFsSourceContractTests(unittest.TestCase):
    def test_sd_boot_path_uses_result_returning_libnx_fs_without_aborting_global_mount(self):
        main_cpp = (ROOT / 'sysmodule/source/main.cpp').read_text(encoding='utf-8')
        store_cpp = (ROOT / 'sysmodule/source/config/sd_config_store.cpp').read_text(encoding='utf-8')
        self.assertNotIn('fs::InitializeForSystem()', main_cpp)
        self.assertNotIn('fs::MountSdCard(', main_cpp)
        self.assertNotIn('fs::Unmount(', main_cpp)
        self.assertIn('fsInitialize()', main_cpp)
        self.assertIn('fsOpenSdCardFileSystem', main_cpp)
        self.assertIn('fsFsClose', main_cpp)
        self.assertIn('fsFsOpenFile', store_cpp)
        self.assertIn('fsFileGetSize', store_cpp)
        self.assertIn('fsFileRead', store_cpp)
        self.assertIn('fsFileClose', store_cpp)

    def test_npdm_service_acl_matches_phase0_runtime_dependencies(self):
        npdm = json.loads((ROOT / 'sysmodule/config/exefs.nsp.json').read_text(encoding='utf-8'))
        self.assertEqual(set(npdm['service_access']), {'fsp-srv', 'bsd:u'})
        self.assertEqual(set(npdm['service_host']), {'nxl:ctl', 'bsd:u'})
        self.assertNotIn('set:sys', npdm['service_access'])


if __name__ == '__main__':
    unittest.main()
