import importlib.util
import json
import socket
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_hardware.py"
spec = importlib.util.spec_from_file_location("phase0_hardware", SCRIPT)
phase0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase0)


class Phase0HardwareTests(unittest.TestCase):
    def test_record_switch_build_rejects_record_bound_to_other_commit(self):
        record = phase0.new_record(Path(__file__).resolve().parents[2])
        record["build"]["nxless_commit"] = "0" * 40
        updated, blockers = phase0.record_switch_build(record, Path(__file__).resolve().parents[2], builder="tester")
        self.assertTrue(any("record commit does not match current HEAD" in b for b in blockers))
        self.assertFalse(updated["build"]["clean_switch_build"])
        self.assertEqual(updated["build"]["package_sha256"], "")

    def test_failed_record_switch_build_preserves_existing_verified_evidence_atomically(self):
        record = phase0.synthetic_complete_record()
        before = json.loads(json.dumps(record))
        record["build"]["nxless_commit"] = "0" * 40
        before = json.loads(json.dumps(record))
        updated, blockers = phase0.record_switch_build(record, Path(__file__).resolve().parents[2], builder="tester")
        self.assertTrue(blockers)
        self.assertEqual(updated, before)

    def test_record_switch_build_hashes_fresh_fixed_package(self):
        from unittest.mock import patch
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "output").mkdir()
            current_commit = "1" * 40
            record = phase0.synthetic_complete_record()
            record["build"].update({
                "nxless_commit": current_commit,
                "package_sha256": "",
                "clean_switch_build": False,
                "source_tree_clean": True,
            })

            def fake_git(_repo, *args):
                if args == ("rev-parse", "HEAD"):
                    return current_commit
                if args == ("status", "--porcelain"):
                    return ""
                return ""

            def fake_gate(command, env=None):
                if command[:2] == ["make", "-C"] and "switch-package" in command:
                    (repo / "output" / "NXless-phase0.zip").write_bytes(b"fresh-package")
                return "pass", "ok"

            ready = {
                "ready": True,
                "blockers": [],
                "toolchain_gate": "pass",
                "toolchain_output": "devkitA64 r30 / libnx 4.12.0-1",
                "atmosphere_gate": "pass",
                "atmosphere_output": "Atmosphere source PASS",
            }
            with patch.object(phase0, "_git", side_effect=fake_git), \
                 patch.object(phase0, "preflight", return_value=ready), \
                 patch.object(phase0, "_run_gate", side_effect=fake_gate):
                updated, blockers = phase0.record_switch_build(record, repo, builder="tester")
            self.assertEqual(blockers, [])
            self.assertTrue(updated["build"]["clean_switch_build"])
            self.assertTrue(updated["build"]["switch_toolchain_verified"])
            self.assertTrue(updated["build"]["atmosphere_source_verified"])
            self.assertEqual(updated["build"]["builder"], "tester")
            self.assertEqual(updated["build"]["package_sha256"], phase0.sha256_file(repo / "output" / "NXless-phase0.zip"))

    def test_tcp_and_udp_echo(self):
        server = phase0.EchoServer("127.0.0.1", tcp_port=0, udp_port=0)
        server.start()
        try:
            with socket.create_connection(("127.0.0.1", server.tcp_port), timeout=2) as s:
                payload = b"nxless-tcp"
                s.sendall(payload)
                self.assertEqual(s.recv(64), payload)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(2)
                payload = b"nxless-udp"
                s.sendto(payload, ("127.0.0.1", server.udp_port))
                data, _ = s.recvfrom(64)
                self.assertEqual(data, payload)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
