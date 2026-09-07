import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "sysmodule" / "source" / "main.cpp"


class MainExitContractTests(unittest.TestCase):
    def test_fail_open_terminal_loop_is_noreturn(self):
        text = MAIN.read_text(encoding="utf-8")
        self.assertIn(
            "void NORETURN IdleFailOpen() noexcept {",
            text,
            "ams::Exit is NORETURN, so its terminal fail-open helper must carry the same contract",
        )
        self.assertIn("void NORETURN Exit(int rc) {", text)
        exit_body = text.split("void NORETURN Exit(int rc) {", 1)[1].split("void Main()", 1)[0]
        self.assertIn("IdleFailOpen();", exit_body)


if __name__ == "__main__":
    unittest.main()
