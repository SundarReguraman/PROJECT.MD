import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class GuidelinesFileTest(unittest.TestCase):
    def test_guidelines_file_is_named_exactly_claude_md(self):
        # os.listdir returns the on-disk case even on case-insensitive filesystems (macOS, Windows),
        # so this catches a Claude.md that Claude Code would not load on Linux or CI.
        names = os.listdir(REPO_ROOT)
        self.assertIn("CLAUDE.md", names)
        self.assertNotIn("Claude.md", names)

    def test_guidelines_start_with_their_title(self):
        first_line = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()[0]
        self.assertTrue(first_line.startswith("# CLAUDE.md"), first_line)


if __name__ == "__main__":
    unittest.main()
