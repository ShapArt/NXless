import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-atmosphere-source.sh"
EXACT_COMMIT = "5388824be146a89619e8d641acd64599cf1c5f62"
PREFIX_COLLISION = "5388824aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def write_exe(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


class AtmosphereSourceGateTests(unittest.TestCase):
    def run_gate(self, head: str, *, include_stratosphere: bool = True):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "Atmosphere"
            (source / ".git").mkdir(parents=True)
            if include_stratosphere:
                marker = source / "libraries/config/templates/stratosphere.mk"
                marker.parent.mkdir(parents=True)
                marker.write_text("# pinned marker\n", encoding="utf-8")

            bin_dir = base / "bin"
            write_exe(
                bin_dir / "git",
                "#!/bin/sh\n"
                "if [ \"$1\" = \"-C\" ] && [ \"$3\" = \"rev-parse\" ] && [ \"$4\" = \"HEAD\" ]; then\n"
                "  printf '%s\\n' \"$FAKE_ATMOSPHERE_HEAD\"\n"
                "  exit 0\n"
                "fi\n"
                "exit 1\n",
            )
            env = os.environ.copy()
            env["FAKE_ATMOSPHERE_HEAD"] = head
            env["PATH"] = str(bin_dir) + os.pathsep + "/usr/bin:/bin"
            return subprocess.run(
                [str(SCRIPT), str(source)],
                env=env,
                capture_output=True,
                text=True,
            )

    def test_accepts_only_exact_full_atmosphere_commit_and_emits_machine_identity(self):
        result = self.run_gate(EXACT_COMMIT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            f'Atmosphere source: commit="{EXACT_COMMIT}"',
        )

    def test_rejects_commit_that_only_matches_short_prefix(self):
        result = self.run_gate(PREFIX_COLLISION)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"expected Atmosphere 1.11.2 commit {EXACT_COMMIT}", result.stderr)

    def test_rejects_missing_stratosphere_marker(self):
        result = self.run_gate(EXACT_COMMIT, include_stratosphere=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing pinned stratosphere.mk", result.stderr)


if __name__ == "__main__":
    unittest.main()
