import unittest
from pathlib import Path


class Phase0AllocatorBoundContractTests(unittest.TestCase):
    def test_sysmodule_allocator_capacity_is_fixed_at_two_mib(self):
        repo = Path(__file__).resolve().parents[2]
        source = (repo / "sysmodule" / "source" / "main.cpp").read_text(encoding="utf-8")

        self.assertIn("constexpr std::size_t kMallocBufferSize = 2_MB;", source)
        self.assertIn("g_malloc_buffer[kMallocBufferSize]", source)
        self.assertIn("init::InitializeAllocator(g_malloc_buffer, sizeof(g_malloc_buffer));", source)


if __name__ == "__main__":
    unittest.main()
