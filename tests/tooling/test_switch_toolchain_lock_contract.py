import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "third_party" / "locks" / "switch-toolchain.lock"
VERIFIER = ROOT / "scripts" / "verify-dependency-lock.py"

EXPECTED = {
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


def parse_lock(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


class SwitchToolchainLockContractTests(unittest.TestCase):
    def test_exact_r30_bytes_are_checked_in_as_a_lock(self):
        self.assertTrue(LOCK.is_file(), f"missing lock: {LOCK}")
        data = parse_lock(LOCK.read_text(encoding="utf-8"))
        for key, value in EXPECTED.items():
            self.assertEqual(data.get(key), value, key)

    def test_common_dependency_verifier_enforces_the_switch_toolchain_lock(self):
        text = VERIFIER.read_text(encoding="utf-8")
        self.assertIn("SWITCH_TOOLCHAIN_LOCK", text)
        self.assertIn("verify_switch_toolchain_lock", text)
        for digest in (value for key, value in EXPECTED.items() if key.endswith(".sha256")):
            self.assertIn(digest, text)


if __name__ == "__main__":
    unittest.main()
