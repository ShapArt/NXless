import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class HorizonFsCompileContractTests(unittest.TestCase):
    def test_sd_config_store_compiles_against_pinned_libnx_style_fs_signatures(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / 'sd_config_store.o'
            cmd = [
                'g++', '-std=c++20', '-DATMOSPHERE_OS_HORIZON',
                '-Wall', '-Wextra', '-Wpedantic', '-Wconversion', '-Wsign-conversion', '-Werror',
                '-I', str(ROOT / 'tests/tooling/horizon_fs_shim'),
                '-I', str(ROOT / 'common/include'),
                '-I', str(ROOT / 'sysmodule/include'),
                '-c', str(ROOT / 'sysmodule/source/config/sd_config_store.cpp'),
                '-o', str(output),
            ]
            completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertTrue(output.exists())


if __name__ == '__main__':
    unittest.main()
