import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "sysmodule" / "Makefile"


class SwitchLtoWarningPolicyTests(unittest.TestCase):
    def test_demotes_only_known_atmosphere_gcc16_lto_false_positive(self):
        text = MAKEFILE.read_text(encoding="utf-8")

        self.assertIn(
            "ATMOSPHERE_SETTINGS += -Wno-error=free-nonheap-object",
            text,
            "GCC 16.1 LTO must keep the pinned Atmosphere free-nonheap diagnostic visible without making it fatal",
        )

        option_tokens = set(re.findall(r"(?<!\\S)-[^\\s]+", text))
        self.assertNotIn("-Wno-free-nonheap-object", option_tokens)
        self.assertNotIn("-Wno-error", option_tokens)
        self.assertNotIn("-w", option_tokens)
        self.assertNotIn("-fno-lto", option_tokens)


if __name__ == "__main__":
    unittest.main()
