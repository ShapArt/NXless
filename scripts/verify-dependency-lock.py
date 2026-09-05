#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

EXPECTED = {
    "atmosphere.version": "1.11.2",
    "atmosphere.commit": "5388824",
    "libnx.version": "4.12.0",
    "libnx.commit": "7644c9b26099aa2d2145bc72a21ee24190e92085",
    "devkitA64.version": "r30",
    "catch2.version": "3.16.0",
    "catch2.commit": "317ac1ed4c0bb6e6b91eafc817e05c488feffcb3",
}

LOCKS = {
    "atmosphere": Path("third_party/locks/atmosphere.lock"),
    "libnx": Path("third_party/locks/libnx.lock"),
    "catch2": Path("third_party/locks/catch2.lock"),
}
CI_LOCK = Path("third_party/locks/ci.lock")
SWITCH_TOOLCHAIN_LOCK = Path("third_party/locks/switch-toolchain.lock")

ALLOWED_SOURCES = {
    "atmosphere": ("github.com", "/Atmosphere-NX/Atmosphere"),
    "libnx": ("github.com", "/switchbrew/libnx"),
    "catch2": ("github.com", "/catchorg/Catch2"),
}

CI_EXPECTED = {
    "actions_checkout.version": "7.0.1",
    "actions_checkout.commit": "3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions_checkout.source": "https://github.com/actions/checkout",
    "actions_upload_artifact.version": "7.0.1",
    "actions_upload_artifact.commit": "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    "actions_upload_artifact.source": "https://github.com/actions/upload-artifact",
    "cmake.version": "4.4.3",
    "cmake.linux_x86_64_sha256": "d6c83076c575bc00b823522ac974bda66d0af05d6ddc30e739c12385cf32c6cc",
    "cmake.source": "https://github.com/Kitware/CMake",
    "host_container.base": "debian:trixie-20260824-slim@sha256:d7e12182ce18b85b93007c1dedf31f2d29e01ccf3182cc4017c709b6259bc132",
}

SWITCH_TOOLCHAIN_EXPECTED = {
    "bootstrap.image": "devkitpro/devkita64:20260219@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282",
    "devkitA64.package": "devkitA64-r30-1-any.pkg.tar.zst",
    "devkitA64.sha256": "66f100490dafe506495ee083bc932aa2c2f231b5dafaa2b203d1832389b700e9",
    "binutils.package": "devkita64-binutils-2.46.0-1-x86_64.pkg.tar.zst",
    "binutils.sha256": "0d61ad4946eb1080c6e645c41f0cfaac0a2eba5fec88426fef8f03363e933b5a",
    "gcc.package": "devkita64-gcc-16.1.0-1-x86_64.pkg.tar.zst",
    "gcc.sha256": "8192b899f0a5fcfe10d11fa63a631b45310c0c8f0b98d88c7c283c16e9d6b0fa",
    "newlib.package": "devkita64-newlib-4.6.0.20260123-4-any.pkg.tar.zst",
    "newlib.sha256": "fc97ba1009a94b68f8714c3cc548ef697ca82687b72fe0c05a7ca3df81beb53e",
    "libnx.package": "libnx-4.12.0-1-any.pkg.tar.zst",
    "libnx.sha256": "c6950bdf8e4b872ece492225368c03e633776329548a7494f91aa1e8f239cd8a",
}

HEX_COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class LockError(ValueError):
    pass


def parse_lock(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise LockError(f"{path}:{line_no}: malformed line")
        key, value = (part.strip() for part in line.split("=", 1))
        if not key or not value:
            raise LockError(f"{path}:{line_no}: empty key/value")
        if key in result:
            raise LockError(f"{path}:{line_no}: duplicate key {key}")
        result[key] = value
    return result


def verify_source(name: str, source: str) -> None:
    parsed = urlparse(source)
    expected_host, expected_path = ALLOWED_SOURCES[name]
    if parsed.scheme != "https" or parsed.netloc != expected_host or parsed.path.rstrip("/") != expected_path:
        raise LockError(f"{name}: unexpected source {source}")


def verify_ci_lock(root: Path) -> str:
    data = parse_lock(root / CI_LOCK)
    for key, expected in CI_EXPECTED.items():
        actual = data.get(key)
        if actual != expected:
            raise LockError(f"ci.{key}: expected {expected}, got {actual!r}")

    if not HEX_COMMIT.fullmatch(data["actions_checkout.commit"]):
        raise LockError("ci: malformed actions_checkout.commit")
    if not HEX_COMMIT.fullmatch(data["actions_upload_artifact.commit"]):
        raise LockError("ci: malformed actions_upload_artifact.commit")
    if not HEX_SHA256.fullmatch(data["cmake.linux_x86_64_sha256"]):
        raise LockError("ci: malformed cmake.linux_x86_64_sha256")

    for key in ("actions_checkout.source", "actions_upload_artifact.source", "cmake.source"):
        parsed = urlparse(data[key])
        if parsed.scheme != "https" or parsed.netloc != "github.com":
            raise LockError(f"ci: unexpected source {data[key]}")

    return (
        "ci: actions/checkout="
        f"{data['actions_checkout.version']}@{data['actions_checkout.commit']} "
        f"upload-artifact={data['actions_upload_artifact.version']}@{data['actions_upload_artifact.commit']} "
        f"cmake={data['cmake.version']} sha256={data['cmake.linux_x86_64_sha256']} source=ok"
    )


def verify_switch_toolchain_lock(root: Path) -> str:
    data = parse_lock(root / SWITCH_TOOLCHAIN_LOCK)
    expected_keys = set(SWITCH_TOOLCHAIN_EXPECTED)
    actual_keys = set(data)
    missing = sorted(expected_keys - actual_keys)
    unexpected = sorted(actual_keys - expected_keys)
    if missing:
        raise LockError(f"switch-toolchain: missing keys {', '.join(missing)}")
    if unexpected:
        raise LockError(f"switch-toolchain: unexpected keys {', '.join(unexpected)}")

    for key, expected in SWITCH_TOOLCHAIN_EXPECTED.items():
        actual = data.get(key)
        if actual != expected:
            raise LockError(f"switch-toolchain.{key}: expected {expected}, got {actual!r}")
        if key.endswith(".sha256") and not HEX_SHA256.fullmatch(actual):
            raise LockError(f"switch-toolchain: malformed {key}")

    return (
        "switch-toolchain: bootstrap=pinned "
        f"devkitA64={data['devkitA64.package']} "
        f"gcc={data['gcc.package']} libnx={data['libnx.package']} sha256=locked"
    )


def verify(root: Path) -> list[str]:
    values: dict[str, str] = {}
    messages: list[str] = []
    for name, rel in LOCKS.items():
        data = parse_lock(root / rel)
        for required in ("version", "commit", "source"):
            if required not in data:
                raise LockError(f"{name}: missing {required}")
        if not HEX_COMMIT.fullmatch(data["commit"]):
            raise LockError(f"{name}: malformed commit")
        verify_source(name, data["source"])
        values[f"{name}.version"] = data["version"]
        values[f"{name}.commit"] = data["commit"]
        if name == "atmosphere":
            if "devkitA64.version" not in data:
                raise LockError("atmosphere: missing devkitA64.version")
            values["devkitA64.version"] = data["devkitA64.version"]
        messages.append(f"{name}: version={data['version']} commit={data['commit']} source=ok")

    for key, expected in EXPECTED.items():
        actual = values.get(key)
        if actual != expected:
            raise LockError(f"{key}: expected {expected}, got {actual!r}")

    messages.append(verify_ci_lock(root))
    messages.append(verify_switch_toolchain_lock(root))
    return messages


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "third_party/locks").mkdir(parents=True)
        for rel in (*LOCKS.values(), CI_LOCK, SWITCH_TOOLCHAIN_LOCK):
            src = Path.cwd() / rel
            (root / rel).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        verify(root)

        duplicate = root / LOCKS["libnx"]
        original = duplicate.read_text(encoding="utf-8")
        duplicate.write_text(original + "version=9.9.9\n", encoding="utf-8")
        try:
            verify(root)
        except LockError as exc:
            assert "duplicate key" in str(exc)
        else:
            raise AssertionError("duplicate key accepted")
        duplicate.write_text(original, encoding="utf-8")

        malformed = root / LOCKS["catch2"]
        original = malformed.read_text(encoding="utf-8")
        malformed.write_text(original.replace(EXPECTED["catch2.commit"], "not-a-sha"), encoding="utf-8")
        try:
            verify(root)
        except LockError as exc:
            assert "malformed commit" in str(exc)
        else:
            raise AssertionError("malformed commit accepted")
        malformed.write_text(original, encoding="utf-8")

        missing = root / LOCKS["atmosphere"]
        original = missing.read_text(encoding="utf-8")
        missing.write_text(
            "\n".join(line for line in original.splitlines() if not line.startswith("version=")) + "\n",
            encoding="utf-8",
        )
        try:
            verify(root)
        except LockError as exc:
            assert "missing version" in str(exc)
        else:
            raise AssertionError("missing key accepted")
        missing.write_text(original, encoding="utf-8")

        ci_lock = root / CI_LOCK
        original = ci_lock.read_text(encoding="utf-8")
        ci_lock.write_text(
            original.replace(CI_EXPECTED["cmake.linux_x86_64_sha256"], "0" * 64),
            encoding="utf-8",
        )
        try:
            verify(root)
        except LockError as exc:
            assert "cmake.linux_x86_64_sha256" in str(exc)
        else:
            raise AssertionError("incorrect CI artifact digest accepted")

        ci_lock.write_text(
            original.replace(CI_EXPECTED["actions_upload_artifact.commit"], "1" * 40),
            encoding="utf-8",
        )
        try:
            verify(root)
        except LockError as exc:
            assert "actions_upload_artifact.commit" in str(exc)
        else:
            raise AssertionError("incorrect upload-artifact pin accepted")
        ci_lock.write_text(original, encoding="utf-8")

        switch_lock = root / SWITCH_TOOLCHAIN_LOCK
        original_switch = switch_lock.read_text(encoding="utf-8")
        switch_lock.write_text(
            original_switch.replace(SWITCH_TOOLCHAIN_EXPECTED["gcc.sha256"], "0" * 64),
            encoding="utf-8",
        )
        try:
            verify(root)
        except LockError as exc:
            assert "switch-toolchain.gcc.sha256" in str(exc)
        else:
            raise AssertionError("incorrect switch toolchain digest accepted")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify NXless pinned dependency lock files")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            run_self_test()
            print("self-test: ok")
        for line in verify(Path.cwd()):
            print(line)
        return 0
    except (OSError, LockError, AssertionError) as exc:
        print(f"dependency-lock verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
