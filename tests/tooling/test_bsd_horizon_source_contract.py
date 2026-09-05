import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICE = (ROOT / 'sysmodule/source/bsd/bsd_mitm_service.cpp').read_text(encoding='utf-8')
SERVICE_HPP = (ROOT / 'sysmodule/include/nxless/sys/bsd/bsd_mitm_service.hpp').read_text(encoding='utf-8')


class HorizonSourceContractTests(unittest.TestCase):
    def test_accept_reinterprets_auto_select_buffer_as_bytes(self):
        self.assertIn('reinterpret_cast<std::byte*>(address.GetPointer())', SERVICE)
        self.assertNotIn('static_cast<std::byte*>(address.GetPointer())', SERVICE)

    def test_every_typed_bsd_hook_raw_forwards_when_tracking_context_is_unavailable(self):
        handlers = ('Socket', 'SocketExempt', 'Accept', 'Close', 'DuplicateSocket')
        for name in handlers:
            match = re.search(
                rf'ams::Result BsdMitmService::{name}\([^{{]+\) noexcept \{{(?P<body>.*?)\n\}}',
                SERVICE,
                re.DOTALL,
            )
            self.assertIsNotNone(match, name)
            self.assertIn('session_.RawPassthroughOnly()', match.group('body'), name)
            self.assertIn('ams::sm::mitm::ResultShouldForwardToSession()', match.group('body'), name)

    def test_typed_hooks_preserve_original_platform_result_before_writing_bsd_outputs(self):
        self.assertEqual(SERVICE.count('if (!result.PlatformSucceeded())'), 5)
        self.assertEqual(SERVICE.count('return ams::Result(result.platform_result);'), 5)

    def test_duplicate_socket_is_a_typed_state_hook(self):
        self.assertIn('AMS_SF_METHOD_INFO(C,H,27,ams::Result,DuplicateSocket', SERVICE_HPP)
        self.assertIn('session_.DuplicateSocket(fd)', SERVICE)

    def test_context_zero_is_named_as_explicit_passthrough_fallback(self):
        self.assertIn('AllocateContextOrPassthrough', SERVICE)
        self.assertNotIn('socket::ClientContextId AllocateContext()', SERVICE)

    def test_generated_sf_interfaces_check_implementations_at_compile_time(self):
        self.assertIn(
            'static_assert(nxless::sys::bsd::IsIBsdMitmService<nxless::sys::bsd::BsdMitmService>)',
            SERVICE_HPP,
        )
        control_hpp = (ROOT / 'sysmodule/include/nxless/sys/ipc/control_service.hpp').read_text(encoding='utf-8')
        self.assertIn(
            'static_assert(nxless::sys::ipc::IsIControlService<nxless::sys::ipc::ControlService>)',
            control_hpp,
        )

    def test_bsd_mitm_manager_does_not_allocate_domain_storage_for_non_domain_bsd_service(self):
        server_hpp = (ROOT / 'sysmodule/include/nxless/sys/bsd/bsd_mitm_server.hpp').read_text(encoding='utf-8')
        self.assertRegex(server_hpp, r'MaxDomains\s*=\s*0\s*;')
        self.assertRegex(server_hpp, r'MaxDomainObjects\s*=\s*0\s*;')

    def test_bsd_mitm_session_capacity_matches_hos_bsd_u_limit(self):
        server_hpp = (ROOT / 'sysmodule/include/nxless/sys/bsd/bsd_mitm_server.hpp').read_text(encoding='utf-8')
        self.assertIn('ServerManager<1,BsdMitmManagerOptions,15>', server_hpp)


if __name__ == '__main__':
    unittest.main()
