import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "docker" / "Dockerfile.host-tests"
CI_LOCK = ROOT / "third_party" / "locks" / "ci.lock"
BASE = "debian:trixie-20260824-slim@sha256:d7e12182ce18b85b93007c1dedf31f2d29e01ccf3182cc4017c709b6259bc132"
CMAKE_SHA256 = "d6c83076c575bc00b823522ac974bda66d0af05d6ddc30e739c12385cf32c6cc"


class HostDockerfileContractTests(unittest.TestCase):
    def _lock(self):
        data = {}
        for raw in CI_LOCK.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            data[key] = value
        return data

    def test_base_image_and_cmake_archive_are_immutable(self):
        text = DOCKERFILE.read_text(encoding="utf-8")
        lock = self._lock()
        self.assertEqual(lock.get("host_container.base"), BASE)
        self.assertEqual(lock.get("cmake.linux_x86_64_sha256"), CMAKE_SHA256)
        self.assertIn(f"FROM {BASE}", text)
        self.assertIn(f"ARG CMAKE_SHA256={CMAKE_SHA256}", text)
        self.assertIn("sha256sum --check --strict", text)

    def test_container_reuses_canonical_repo_target(self):
        text = DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn("python3 scripts/verify-dependency-lock.py --self-test", text)
        self.assertIn("make host-test", text)
        self.assertNotIn("cmake --preset host-debug && cmake --build", text)


if __name__ == "__main__":
    unittest.main()
