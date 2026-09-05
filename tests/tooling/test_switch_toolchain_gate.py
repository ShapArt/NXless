import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-switch-toolchain.sh"


def write_exe(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


class SwitchToolchainGateTests(unittest.TestCase):
    def run_gate(self, libnx_line: str, include_pkg_tool: bool = True):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            devkitpro = base / "devkitpro"
            bin_dir = base / "bin"
            write_exe(
                devkitpro / "devkitA64/bin/aarch64-none-elf-gcc",
                "#!/bin/sh\necho 16.1.0\n",
            )
            if include_pkg_tool:
                write_exe(
                    bin_dir / "dkp-pacman",
                    "#!/bin/sh\n"
                    "if [ \"$1\" = \"-Q\" ] && [ \"$2\" = \"devkitA64\" ]; then echo 'devkitA64 r30-1'; exit 0; fi\n"
                    f"if [ \"$1\" = \"-Q\" ] && [ \"$2\" = \"libnx\" ]; then echo '{libnx_line}'; exit 0; fi\n"
                    "exit 1\n",
                )
            env = os.environ.copy()
            env["DEVKITPRO"] = str(devkitpro)
            env["PATH"] = str(bin_dir) + os.pathsep + "/usr/bin:/bin"
            return subprocess.run([str(SCRIPT)], env=env, capture_output=True, text=True)

    def test_accepts_exact_r30_and_libnx_4120(self):
        result = self.run_gate("libnx 4.12.0-1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            'switch toolchain: devkit_pkg="devkitA64 r30-1"; gcc="16.1.0"; libnx_pkg="libnx 4.12.0-1"',
        )

    def test_rejects_old_libnx_even_with_r30(self):
        result = self.run_gate("libnx 4.11.1-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected libnx 4.12.0-1", result.stderr)

    def test_rejects_suffix_after_exact_libnx_package_version(self):
        result = self.run_gate("libnx 4.12.0-1evil")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected libnx 4.12.0-1", result.stderr)

    def test_rejects_unverifiable_package_set(self):
        result = self.run_gate("", include_pkg_tool=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("package query tool is required", result.stderr)


if __name__ == "__main__":
    unittest.main()
