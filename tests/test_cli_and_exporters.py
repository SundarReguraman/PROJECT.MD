import io
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from project_md import cli
from project_md.agents.orchestrator import Orchestrator
from project_md.exporters import render_all

REPO_ROOT = Path(__file__).resolve().parent.parent
HANDWRITING = "An app to transcribe doctor handwriting"
ALL_FILES = (
    "PROJECT.md",
    "CLAUDE.md",
    ".cursorrules",
    "GEMINI.md",
    ".agent/rules/dead-ends.md",
    ".agent/rules/architecture.md",
    ".agent/rules/contracts.md",
    ".agent/rules/security.md",
    "AGENTS.md",
)


def run_main(argv):
    out = io.StringIO()
    code = cli.main(argv, stdout=out)
    return code, out.getvalue()


class CliSubprocessTest(unittest.TestCase):
    """Runs the real entry point: python3 -m project_md.cli."""

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "project_md.cli", *args],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )

    def test_one_shot_produces_all_context_files_on_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(HANDWRITING, "--out", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ALL_FILES:
                with self.subTest(file=name):
                    path = Path(tmp) / name
                    self.assertTrue(path.is_file(), f"{name} missing")
                    self.assertTrue(path.read_text(encoding="utf-8").strip())

    def test_output_shows_banner_agents_score_and_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = self.run_cli(HANDWRITING, "--out", tmp).stdout
        self.assertIn("PROJECT.MD  Architecture Pre-Flight", stdout)
        for agent in cli.AGENT_ORDER:
            self.assertIn(f"[{agent}]", stdout)
        self.assertRegex(stdout, r"Risk score: \d+/100")
        self.assertIn("Verdict:    REVIEW", stdout)
        self.assertNotIn("\033[", stdout, "no colour codes when not writing to a terminal")

    def test_block_verdict_exits_3_but_still_writes_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("Use OpenCV contours to read handwritten notes", "--out", tmp)
            self.assertEqual(result.returncode, cli.EXIT_BLOCK)
            self.assertIn("Verdict:    BLOCK", result.stdout)
            self.assertTrue((Path(tmp) / "PROJECT.md").is_file())


class CliBehaviourTest(unittest.TestCase):
    def test_prompts_for_idea_when_none_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("builtins.input", return_value=HANDWRITING) as prompt:
                code, out = run_main(["--out", tmp])
            prompt.assert_called_once()
            self.assertIn("What do you want to build?", prompt.call_args[0][0])
            self.assertEqual(code, 0)
            self.assertIn(f"Idea: {HANDWRITING}", out)
            self.assertTrue((Path(tmp) / "CLAUDE.md").is_file())

    def test_empty_or_closed_prompt_is_an_error(self):
        for side_effect in ([""], EOFError()):
            with self.subTest(side_effect=side_effect), tempfile.TemporaryDirectory() as tmp:
                with mock.patch("builtins.input", side_effect=side_effect):
                    code, out = run_main(["--out", tmp])
                self.assertEqual(code, cli.EXIT_ERROR)
                self.assertIn("No idea given", out)
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_existing_files_are_kept_unless_forced(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude = Path(tmp) / "CLAUDE.md"
            claude.write_text("hand-written notes\n", encoding="utf-8")

            _, out = run_main([HANDWRITING, "--out", tmp])
            self.assertEqual(claude.read_text(encoding="utf-8"), "hand-written notes\n")
            self.assertIn("skipped", out)
            self.assertTrue((Path(tmp) / "PROJECT.md").is_file())

            run_main([HANDWRITING, "--out", tmp, "--force"])
            self.assertIn("# CLAUDE.md", claude.read_text(encoding="utf-8"))

    def test_targets_limit_the_files_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_main([HANDWRITING, "--out", tmp, "--targets", "claude,cursor"])
            written = sorted(p.name for p in Path(tmp).iterdir())
            self.assertEqual(written, [".cursorrules", "CLAUDE.md"])

    def test_unknown_target_is_an_error(self):
        code, out = run_main([HANDWRITING, "--no-write", "--targets", "copilot-x"])
        self.assertEqual(code, cli.EXIT_ERROR)
        self.assertIn("unknown target", out)

    def test_no_write_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_main([HANDWRITING, "--out", tmp, "--no-write"])
            self.assertEqual(list(Path(tmp).iterdir()), [])


class ExporterContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = Orchestrator().run_sync("Use OpenCV to read handwritten doctor notes in a web app").report
        cls.files = render_all(cls.report)

    def test_every_file_carries_the_dead_end_and_its_replacement(self):
        for name in ("PROJECT.md", "CLAUDE.md", ".cursorrules", ".agent/rules/dead-ends.md", "AGENTS.md"):
            with self.subTest(file=name):
                self.assertIn("OCR-001", self.files[name])
                self.assertIn("TrOCR", self.files[name])

    def test_every_file_agrees_on_the_stack(self):
        for component in self.report.stack.components:
            for name in ("CLAUDE.md", ".cursorrules", "GEMINI.md", "AGENTS.md"):
                with self.subTest(file=name, role=component.role):
                    self.assertIn(component.choice, self.files[name])

    def test_gemini_index_points_only_at_rule_files_that_exist(self):
        referenced = re.findall(r"`(\.agent/rules/[\w-]+\.md)`", self.files["GEMINI.md"])
        self.assertTrue(referenced)
        for path in referenced:
            self.assertIn(path, self.files)

    def test_native_conventions(self):
        self.assertIn("## Commands", self.files["CLAUDE.md"])
        self.assertIn("Plan mode", self.files["AGENTS.md"])
        self.assertIn("Subagent protocol", self.files["GEMINI.md"])
        self.assertFalse(self.files[".cursorrules"].startswith("#"), ".cursorrules is plain directives, not markdown")

    def test_mixed_stack_lists_frontend_commands(self):
        claude = self.files["CLAUDE.md"]
        self.assertIn("uvicorn", claude)
        self.assertIn("npm run dev", claude)


if __name__ == "__main__":
    unittest.main()
