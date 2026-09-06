import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phase0_build.py"


def load_module():
    spec = importlib.util.spec_from_file_location("phase0_build", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Phase0BuildOrchestratorTests(unittest.TestCase):
    def test_root_makefile_exposes_one_command_phase0_build(self):
        root = Path(__file__).resolve().parents[2]
        text = (root / "Makefile").read_text(encoding="utf-8")
        self.assertIn("phase0-build:", text)
        self.assertIn("scripts/phase0_build.py", text)

    def test_generated_build_inputs_and_evidence_are_gitignored(self):
        root = Path(__file__).resolve().parents[2]
        ignored = {line.strip() for line in (root / ".gitignore").read_text(encoding="utf-8").splitlines()}
        self.assertIn("third_party/Atmosphere/", ignored)
        self.assertIn("evidence/", ignored)

    def test_default_paths_are_repo_owned_and_commit_bound(self):
        mod = load_module()
        repo = Path("/repo")
        commit = "a" * 40
        self.assertEqual(mod.default_atmosphere_root(repo), repo / "third_party" / "Atmosphere")
        self.assertEqual(
            mod.default_record_path(repo, commit),
            repo / "evidence" / "phase0-hardware-aaaaaaaaaaaa.json",
        )

    def test_clean_commit_guard_rejects_dirty_tree(self):
        mod = load_module()
        with patch.object(mod, "_git", side_effect=["a" * 40, " M sysmodule/source/main.cpp"]):
            with self.assertRaisesRegex(mod.BuildError, "dirty"):
                mod.require_clean_commit(Path("/repo"))

    def test_clean_commit_guard_rejects_non_full_sha(self):
        mod = load_module()
        with patch.object(mod, "_git", side_effect=["short", ""]):
            with self.assertRaisesRegex(mod.BuildError, "full git commit"):
                mod.require_clean_commit(Path("/repo"))

    def test_missing_atmosphere_checkout_is_fetched_at_exact_pin(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "Atmosphere"
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)

            with patch.object(mod, "_run_checked", side_effect=fake_run):
                mod.ensure_atmosphere_checkout(Path("/repo"), root, fetch_missing=True)

            self.assertEqual(calls[0], ["git", "init", str(root)])
            self.assertEqual(calls[1], ["git", "-C", str(root), "remote", "add", "origin", mod.ATMOSPHERE_URL])
            self.assertEqual(calls[2], ["git", "-C", str(root), "fetch", "--depth", "1", "origin", "tag", mod.ATMOSPHERE_TAG])
            self.assertEqual(calls[3], ["git", "-C", str(root), "checkout", "--detach", "FETCH_HEAD"])
            self.assertEqual(calls[4], [str(Path("/repo") / "scripts" / "verify-atmosphere-source.sh"), str(root)])

    def test_missing_atmosphere_checkout_can_be_forbidden(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "Atmosphere"
            with self.assertRaisesRegex(mod.BuildError, "missing pinned Atmosphere checkout"):
                mod.ensure_atmosphere_checkout(Path("/repo"), root, fetch_missing=False)

    def test_existing_record_is_not_overwritten(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            record = repo / "evidence" / "phase0-hardware-aaaaaaaaaaaa.json"
            record.parent.mkdir(parents=True)
            record.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(mod.BuildError, "already exists"):
                mod.require_new_record_path(record)

    def test_pipeline_orders_verification_before_switch_build(self):
        mod = load_module()
        commit = "b" * 40
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            atmosphere = repo / "third_party" / "Atmosphere"
            atmosphere.mkdir(parents=True)
            (atmosphere / ".git").mkdir()
            record = repo / "evidence" / "record.json"
            calls = []

            def fake_run(command, *, env=None, cwd=None):
                calls.append((command, dict(env or {}), cwd))
                if "new-record" in command:
                    record.parent.mkdir(parents=True, exist_ok=True)
                    record.write_text("{}\n", encoding="utf-8")

            with patch.object(mod, "require_clean_commit", return_value=commit), \
                 patch.object(mod, "ensure_atmosphere_checkout"), \
                 patch.object(mod, "_run_checked", side_effect=fake_run):
                result = mod.run_pipeline(repo, atmosphere, record, builder="tester", fetch_atmosphere=False)

            commands = [item[0] for item in calls]
            self.assertEqual(commands[0], ["make", "-C", str(repo), "hardware-tool-test"])
            self.assertIn("new-record", commands[1])
            self.assertIn("record-host", commands[2])
            self.assertIn("record-build", commands[3])
            self.assertEqual(result, record)
            for _, env, _ in calls:
                self.assertEqual(env.get("NXLESS_ATMOSPHERE_ROOT"), str(atmosphere))


if __name__ == "__main__":
    unittest.main()
