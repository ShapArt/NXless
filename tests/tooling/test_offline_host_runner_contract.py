import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class OfflineHostRunnerContractTests(unittest.TestCase):
    def test_makefile_exposes_offline_sanitizer_target(self):
        makefile = (ROOT / 'Makefile').read_text(encoding='utf-8')
        self.assertIn('host-test-offline:', makefile)
        self.assertIn('scripts/run-host-tests-offline.sh', makefile)

    def test_offline_runner_tracks_all_cmake_unit_test_sources(self):
        cmake = (ROOT / 'tests/CMakeLists.txt').read_text(encoding='utf-8')
        block = re.search(r'add_executable\(nxless_unit_tests(?P<body>.*?)\n\)', cmake, re.DOTALL)
        self.assertIsNotNone(block)
        sources = [line.strip() for line in block.group('body').splitlines() if line.strip()]
        runner = (ROOT / 'scripts/run-host-tests-offline.sh').read_text(encoding='utf-8')
        for source in sources:
            self.assertIn(source, runner, source)

    def test_offline_runner_tracks_all_common_library_sources(self):
        cmake = (ROOT / 'common/CMakeLists.txt').read_text(encoding='utf-8')
        block = re.search(r'add_library\(nxless_common STATIC(?P<body>.*?)\n\)', cmake, re.DOTALL)
        self.assertIsNotNone(block)
        sources = [line.strip() for line in block.group('body').splitlines() if line.strip()]
        runner = (ROOT / 'scripts/run-host-tests-offline.sh').read_text(encoding='utf-8')
        for source in sources:
            self.assertIn(source, runner, source)


if __name__ == '__main__':
    unittest.main()
