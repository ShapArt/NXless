#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path

TITLE_ID = "0100000000004E58"
ALLOWED_FILES = {
    f"atmosphere/contents/{TITLE_ID}/exefs.nsp",
    f"atmosphere/contents/{TITLE_ID}/flags/boot2.flag",
    "config/nxless/example.toml",
}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".nro", ".ovl"}
SUBSCRIPTION_RE = re.compile(r"https?://[^\s\"']*(?:subscr|subscription|subscribe)[^\s\"']*", re.I)


def _rel_files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def verify(root: Path, repository_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"package root does not exist: {root}"]

    files = _rel_files(root)
    actual = set(files)
    missing = ALLOWED_FILES - actual
    unexpected = actual - ALLOWED_FILES
    if missing:
        errors.append("missing required files: " + ", ".join(sorted(missing)))
    if unexpected:
        errors.append("unexpected package files: " + ", ".join(sorted(unexpected)))

    for rel in files:
        path = root / rel
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden artifact type: {rel}")
        if path.stat().st_size > 4 * 1024 * 1024 and path.name != "exefs.nsp":
            errors.append(f"unexpected oversized non-binary file: {rel}")
            continue
        if path.name == "exefs.nsp":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"unexpected binary file: {rel}")
            continue
        lower = text.lower()
        if "vless://" in lower:
            errors.append(f"real or example VLESS URI is forbidden in Phase 0 package: {rel}")
        if SUBSCRIPTION_RE.search(text):
            errors.append(f"subscription URL is forbidden in Phase 0 package: {rel}")
        if "private_key" in lower or "private-key" in lower:
            errors.append(f"private-key material marker is forbidden: {rel}")

    if repository_root is not None:
        recovery = repository_root / "docs" / "recovery.md"
        if not recovery.is_file():
            errors.append("missing repository recovery document: docs/recovery.md")
        else:
            text = recovery.read_text(encoding="utf-8").lower()
            required = [
                "/config/nxless/disable.flag",
                f"/atmosphere/contents/{TITLE_ID.lower()}",
                "power off",
                "normal networking",
                "nand",
                "not hardware-proven",
            ]
            for needle in required:
                if needle not in text:
                    errors.append(f"recovery document missing required concept: {needle}")
    return errors


def _write_good(root: Path) -> None:
    (root / f"atmosphere/contents/{TITLE_ID}/flags").mkdir(parents=True)
    (root / "config/nxless").mkdir(parents=True)
    (root / f"atmosphere/contents/{TITLE_ID}/exefs.nsp").write_bytes(b"NXLESS-SYNTHETIC-PHASE0")
    (root / f"atmosphere/contents/{TITLE_ID}/flags/boot2.flag").write_bytes(b"")
    (root / "config/nxless/example.toml").write_text(
        '# Phase 0 has no proxy profile or secrets.\nmode = "transparent"\n', encoding="utf-8"
    )


def self_test() -> int:
    cases = 0
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        good = base / "good"
        _write_good(good)
        assert verify(good) == []
        cases += 1

        bad_extra = base / "bad-extra"
        _write_good(bad_extra)
        (bad_extra / "switch/NXless").mkdir(parents=True)
        (bad_extra / "switch/NXless/NXless.nro").write_bytes(b"x")
        assert any("unexpected package files" in e for e in verify(bad_extra))
        assert any("forbidden artifact type" in e for e in verify(bad_extra))
        cases += 1

        bad_secret = base / "bad-secret"
        _write_good(bad_secret)
        (bad_secret / "config/nxless/example.toml").write_text('server="vless://uuid@example.invalid"\n', encoding="utf-8")
        assert any("VLESS" in e for e in verify(bad_secret))
        cases += 1

        bad_key = base / "bad-key"
        _write_good(bad_key)
        (bad_key / "config/nxless/example.toml").write_text('private_key="secret"\n', encoding="utf-8")
        assert any("private-key" in e for e in verify(bad_key))
        cases += 1

        bad_missing = base / "bad-missing"
        _write_good(bad_missing)
        (bad_missing / f"atmosphere/contents/{TITLE_ID}/flags/boot2.flag").unlink()
        assert any("missing required files" in e for e in verify(bad_missing))
        cases += 1

        bad_subscription = base / "bad-subscription"
        _write_good(bad_subscription)
        (bad_subscription / "config/nxless/example.toml").write_text('url="https://example.invalid/subscription/token"\n', encoding="utf-8")
        assert any("subscription URL" in e for e in verify(bad_subscription))
        cases += 1

        bad_pem = base / "bad-pem"
        _write_good(bad_pem)
        (bad_pem / "config/nxless/client.pem").write_text("synthetic certificate fixture\n", encoding="utf-8")
        assert any("forbidden artifact type" in e for e in verify(bad_pem))
        cases += 1

        bad_key_file = base / "bad-key-file"
        _write_good(bad_key_file)
        (bad_key_file / "config/nxless/client.key").write_text("synthetic key fixture\n", encoding="utf-8")
        assert any("forbidden artifact type" in e for e in verify(bad_key_file))
        cases += 1

        fake_repo = base / "repo-without-recovery"
        fake_repo.mkdir()
        assert any("missing repository recovery document" in e for e in verify(good, fake_repo))
        cases += 1

    print(f"verify-phase0-package self-test: PASS ({cases} cases)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", nargs="?", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.package is None:
        parser.error("package path is required unless --self-test is used")
    errors = verify(args.package, args.repo_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Phase 0 package verification: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
