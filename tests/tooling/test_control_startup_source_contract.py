import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = (ROOT / 'sysmodule/source/main.cpp').read_text(encoding='utf-8')


class ControlStartupSourceContractTests(unittest.TestCase):
    def test_thread_is_created_before_control_service_is_published(self):
        start = MAIN.index('bool StartControlService() noexcept')
        end = MAIN.index('\n}\n\n} // namespace', start)
        body = MAIN[start:end]
        self.assertLess(body.index('os::CreateThread('), body.index('RegisterObjectForServer('))

    def test_registration_failure_destroys_unstarted_thread(self):
        start = MAIN.index('bool StartControlService() noexcept')
        end = MAIN.index('\n}\n\n} // namespace', start)
        body = MAIN[start:end]
        self.assertIn('os::DestroyThread(&g_control_thread)', body)

    def test_control_service_allocation_is_checked_before_registration(self):
        start = MAIN.index('bool StartControlService() noexcept')
        end = MAIN.index('\n}\n\n} // namespace', start)
        body = MAIN[start:end]
        self.assertIn('if (service == nullptr)', body)
        self.assertLess(body.index('if (service == nullptr)'), body.index('RegisterObjectForServer('))


if __name__ == '__main__':
    unittest.main()
