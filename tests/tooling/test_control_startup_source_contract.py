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

class ControlStatusConcurrencySourceContractTests(unittest.TestCase):
    def test_main_uses_atomic_control_state_instead_of_raw_runtime_globals(self):
        self.assertIn('nxless::ipc::ControlState g_control_state', MAIN)
        self.assertNotIn('g_runtime_mode', MAIN)
        self.assertNotIn('g_last_internal_error', MAIN)

    def test_control_state_is_initialized_before_service_thread_can_run(self):
        self.assertLess(
            MAIN.index('g_control_state.SetMode(pre_control_decision.mode)'),
            MAIN.index('const bool control_available = StartControlService()'),
        )
