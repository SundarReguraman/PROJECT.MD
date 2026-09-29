import os
import re
import unittest
from pathlib import Path

from project_md import cli
from project_md.core.knowledge_base import TRAPS
from project_md.core.models import Category
from project_md.exporters import EXPORTERS

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


class PackagingTest(unittest.TestCase):
    def test_pyproject_license_is_an_spdx_string_matching_licence_file(self):
        # The TOML-table form (license = { file = ... }) is deprecated by setuptools; removal after 2027-02-18.
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        licence = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8").split()[0]  # e.g. "MIT"
        self.assertRegex(pyproject, r'(?m)^license = "%s"$' % re.escape(licence))
        self.assertRegex(pyproject, r'setuptools>=(7[7-9]|[89]\d)')


class ReadmeTest(unittest.TestCase):
    """Issue #6: the README must describe this product and stay in sync with it."""

    @classmethod
    def setUpClass(cls):
        cls.readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    def test_licence_matches_licence_file(self):
        licence = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8").splitlines()[0]  # e.g. "MIT License"
        self.assertIn(f"[{licence.split()[0]}](LICENSE)", self.readme)
        self.assertNotIn("Apache", self.readme)

    def test_local_links_and_paths_exist(self):
        for path in re.findall(r"\]\(((?!https?:)[^)#]+)\)", self.readme):
            with self.subTest(path=path):
                self.assertTrue((REPO_ROOT / path).exists(), path)
        for path in ("project_md/core/knowledge_base.py", "tests/test_knowledge_base.py", "docs/demo/demo.tape"):
            with self.subTest(path=path):
                self.assertIn(path, self.readme)
                self.assertTrue((REPO_ROOT / path).exists(), path)

    def test_trap_and_domain_counts_are_current(self):
        match = re.search(r"holds (\d+) traps across (\d+) domains", self.readme)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), len(TRAPS))
        self.assertEqual(int(match.group(2)), len(Category))

    def test_targets_and_exit_codes_match_the_cli(self):
        self.assertIn("comma-separated subset: " + ", ".join(t.value for t in EXPORTERS), self.readme)
        self.assertIn(f"| `{cli.EXIT_BLOCK}` |", self.readme)
        self.assertIn(f"Exit code `{cli.EXIT_ERROR}` means an error", self.readme)

    def test_no_references_to_the_old_concept(self):
        for stale in ("backend/", "frontend/", "requirements.txt", "uvicorn", "IBM Bob 2.0"):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, self.readme)


if __name__ == "__main__":
    unittest.main()
