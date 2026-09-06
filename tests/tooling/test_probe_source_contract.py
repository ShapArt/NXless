import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = (ROOT / "tools/hardware_probe/source/main.cpp").read_text(encoding="utf-8")
MAKE = (ROOT / "tools/hardware_probe/Makefile").read_text(encoding="utf-8")
PACKAGE = (ROOT / "scripts/verify-phase0-package.py").read_text(encoding="utf-8")


class ProbeSourceContractTests(unittest.TestCase):
    def test_queries_only_read_only_phase0_control_commands(self):
        self.assertIn('smGetService(&ctl, "nxl:ctl")', MAIN)
        self.assertIn('serviceDispatchOut(&ctl, 0, version)', MAIN)
        self.assertIn('serviceDispatchOut(&ctl, 1, compatibility)', MAIN)
        self.assertIn('serviceDispatchOut(&ctl, 2, status)', MAIN)
        self.assertNotIn('serviceDispatchOut(&ctl, 3,', MAIN)

    def test_exercises_both_tcp_and_udp_through_normal_socket_runtime(self):
        self.assertIn('socketInitializeDefault()', MAIN)
        self.assertIn('SOCK_STREAM', MAIN)
        self.assertIn('SOCK_DGRAM', MAIN)
        self.assertIn('connect(', MAIN)
        self.assertIn('sendto(', MAIN)
        self.assertIn('recvfrom(', MAIN)

    def test_probe_is_test_only_and_not_release_material(self):
        self.assertIn('TARGET      := NXlessProbe', MAKE)
        self.assertIn('NO_ICON     := 1', MAKE)
        self.assertIn('-fno-rtti -fno-exceptions', MAKE)
        self.assertIn('".nro"', PACKAGE)
        self.assertNotIn('NXlessProbe', (ROOT / 'sysmodule/Makefile').read_text(encoding='utf-8'))

    def test_nacp_metadata_is_defined_before_switch_rules(self):
        include_pos = MAKE.index('include $(DEVKITPRO)/libnx/switch_rules')
        self.assertLess(MAKE.index('APP_TITLE'), include_pos)
        self.assertLess(MAKE.index('APP_AUTHOR'), include_pos)
        self.assertLess(MAKE.index('APP_VERSION'), include_pos)

    def test_baseline_control_absence_is_not_reported_as_failure(self):
        self.assertIn('ctl=%s', MAIN)
        self.assertIn('"UNAVAILABLE"', MAIN)
        self.assertNotIn('ctl_ok_before ? "PASS" : "FAIL"', MAIN)

    def test_successful_echo_does_not_print_stale_errno(self):
        self.assertNotIn('TCP echo: %s (errno=%d)', MAIN)
        self.assertNotIn('UDP echo: %s (errno=%d)', MAIN)

    def test_probe_source_contains_no_proxy_or_secret_material(self):
        lower = MAIN.lower()
        for forbidden in ('vless://', 'private_key', 'private-key', 'subscription'):
            self.assertNotIn(forbidden, lower)


if __name__ == '__main__':
    unittest.main()
