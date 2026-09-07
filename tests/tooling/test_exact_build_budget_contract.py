import re
import unittest
from pathlib import Path

from scripts.phase0_hw import build_gates


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "toolchain-probe.yml"


class ExactBuildBudgetContractTests(unittest.TestCase):
    def test_clean_switch_package_has_thirty_minute_budget(self):
        self.assertGreaterEqual(
            build_gates.SWITCH_PACKAGE_GATE_TIMEOUT_SECONDS,
            30 * 60,
            "the pinned Atmosphere clean build has already been observed taking more than 20 minutes on GitHub runners",
        )

    def test_exact_job_leaves_fifteen_minutes_beyond_inner_build_budget(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        match = re.search(r"(?m)^\s+timeout-minutes:\s*(\d+)\s*$", text)
        self.assertIsNotNone(match, "exact-r30 workflow must have a bounded job timeout")
        job_timeout_seconds = int(match.group(1)) * 60
        self.assertGreaterEqual(
            job_timeout_seconds,
            build_gates.SWITCH_PACKAGE_GATE_TIMEOUT_SECONDS + 15 * 60,
            "outer exact-r30 job must leave room for toolchain setup, probe build, and artifact upload",
        )


if __name__ == "__main__":
    unittest.main()
