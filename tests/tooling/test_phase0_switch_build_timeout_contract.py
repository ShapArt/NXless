import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from phase0_hw import build_gates, gate_common, report


class Phase0SwitchBuildTimeoutContractTests(unittest.TestCase):
    def test_switch_package_build_has_separate_bounded_long_deadline(self):
        self.assertGreater(
            build_gates.SWITCH_PACKAGE_GATE_TIMEOUT_SECONDS,
            gate_common.DEFAULT_GATE_TIMEOUT_SECONDS,
        )
        self.assertLessEqual(build_gates.SWITCH_PACKAGE_GATE_TIMEOUT_SECONDS, 30 * 60)

        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "output").mkdir()
            commit = "1" * 40
            record = report.synthetic_complete_record()
            record["build"].update(
                {
                    "nxless_commit": commit,
                    "package_sha256": "",
                    "clean_switch_build": False,
                    "source_tree_clean": True,
                    "observed_devkitA64_package": "",
                    "observed_gcc_version": "",
                    "observed_libnx_package": "",
                    "observed_atmosphere_commit": "",
                }
            )

            def fake_git(_repo, *args):
                if args == ("rev-parse", "HEAD"):
                    return commit
                if args == ("status", "--porcelain"):
                    return ""
                return ""

            ready = {
                "ready": True,
                "blockers": [],
                "toolchain_gate": "pass",
                "toolchain_output": (
                    'switch toolchain: devkit_pkg="devkitA64 r30-1"; '
                    'gcc="16.1.0"; libnx_pkg="libnx 4.12.0-1"'
                ),
                "atmosphere_gate": "pass",
                "atmosphere_output": (
                    'Atmosphere source: commit="5388824be146a89619e8d641acd64599cf1c5f62"'
                ),
            }
            calls = []

            def fake_gate(command, env=None, **kwargs):
                calls.append((list(command), dict(kwargs)))
                if "switch-package" in command:
                    (repo / "output" / "NXless-phase0.zip").write_bytes(b"package")
                return "pass", "ok"

            updated, blockers = build_gates.record_switch_build(
                record,
                repo,
                builder="tester",
                git_fn=fake_git,
                preflight_fn=lambda _repo: ready,
                run_gate=fake_gate,
            )

            self.assertEqual(blockers, [])
            self.assertTrue(updated["build"]["clean_switch_build"])
            switch_calls = [entry for entry in calls if "switch-package" in entry[0]]
            self.assertEqual(len(switch_calls), 1)
            self.assertEqual(
                switch_calls[0][1].get("timeout_seconds"),
                build_gates.SWITCH_PACKAGE_GATE_TIMEOUT_SECONDS,
            )
            clean_calls = [entry for entry in calls if "clean" in entry[0]]
            self.assertEqual(len(clean_calls), 1)
            self.assertNotIn("timeout_seconds", clean_calls[0][1])


if __name__ == "__main__":
    unittest.main()
