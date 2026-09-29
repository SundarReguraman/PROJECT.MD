"""PROJECT.MD command-line interface.

    python3 -m project_md.cli "An app to transcribe doctor handwriting"
    python3 -m project_md.cli                    # prompts for the idea

Exit codes: 0 PASS or REVIEW, 1 error, 3 BLOCK (argparse uses 2 for usage errors).
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, TextIO

from project_md import __version__
from project_md.agents.orchestrator import Orchestrator
from project_md.core.knowledge_base import TRAPS
from project_md.core.models import ContextTarget, Finding, PreflightReport, Severity, Verdict
from project_md.exporters import EXPORTERS, render_all, write_files

EXIT_OK, EXIT_ERROR, EXIT_BLOCK = 0, 1, 3

AGENT_ORDER = ("dependency", "architecture", "contract", "impact", "security")
SEVERITY_TAGS = {Severity.CRITICAL: "CRIT", Severity.WARNING: "WARN", Severity.INFO: "INFO"}
VERDICT_TEXT = {
    Verdict.PASS: "PASS    cleared for implementation",
    Verdict.REVIEW: "REVIEW  resolve the warnings above before building those parts",
    Verdict.BLOCK: "BLOCK   the idea names a known dead end; the files mandate the replacement",
}

LOGO_WIDTH = 34  # Characters between the page's left and right edges.
LOGO_TITLE = "P R O J E C T . M D"
LOGO_FEATURES = (
    "Zero-Prerequisite Engine",
    "Pre-Flight Tech Audit",
    "5-Agent Architecture",
    "Universal Context Exporter",
)
TAGLINE = "Build the right thing before you build it wrong."

# ANSI colours, applied only when writing to a capable terminal.
RED, YELLOW, GREEN, CYAN, WHITE = "\033[31m", "\033[33m", "\033[32m", "\033[36m", "\033[97m"
DIM, BOLD, RESET = "\033[2m", "\033[1m", "\033[0m"
SEVERITY_COLORS = {Severity.CRITICAL: RED, Severity.WARNING: YELLOW, Severity.INFO: DIM}
VERDICT_COLORS = {Verdict.PASS: GREEN, Verdict.REVIEW: YELLOW, Verdict.BLOCK: RED}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project-md",
        description="Pre-flight your idea: catch architectural dead ends and generate AI assistant context files.",
        epilog="Exit codes: 0 PASS/REVIEW, 1 error, 3 BLOCK.",
    )
    parser.add_argument("idea", nargs="*", help="what you want to build, in plain English (prompted if omitted)")
    parser.add_argument("-o", "--out", default=".", help="directory to write the context files to (default: current)")
    parser.add_argument(
        "-t", "--targets",
        help="comma-separated subset of: " + ", ".join(t.value for t in EXPORTERS) + " (default: all)",
    )
    parser.add_argument("-f", "--force", action="store_true", help="overwrite context files that already exist")
    parser.add_argument("--no-write", action="store_true", help="run the pre-flight only; write no files")
    parser.add_argument("--no-color", action="store_true", help="disable coloured output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Optional[List[str]] = None, stdout: Optional[TextIO] = None) -> int:
    out = stdout or sys.stdout
    args = build_parser().parse_args(argv)
    ui = Printer(out, color=not args.no_color and _supports_color(out))

    try:
        targets = _parse_targets(args.targets)
    except ValueError as exc:
        ui.line(f"error: {exc}")
        return EXIT_ERROR

    ui.banner()
    idea = " ".join(args.idea).strip()
    if not idea:
        try:
            idea = input("What do you want to build?\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            ui.line("\nNo idea given. Try: python3 -m project_md.cli \"An app to transcribe doctor handwriting\"")
            return EXIT_ERROR
        if not idea:
            ui.line("No idea given. Describe what you want to build in one sentence.")
            return EXIT_ERROR

    ui.line(f"Idea: {idea}")
    ui.line(f"Running {len(AGENT_ORDER)} specialist agents in parallel...", DIM)
    report = Orchestrator().run_sync(idea).report

    ui.findings(report)
    ui.verdict(report)

    if not args.no_write:
        written, skipped = write_files(render_all(report, targets), args.out, force=args.force)
        ui.files(written, skipped)

    return EXIT_BLOCK if report.verdict is Verdict.BLOCK else EXIT_OK


class Printer:
    def __init__(self, out: TextIO, color: bool):
        self.out = out
        self.color = color

    def line(self, text: str = "", style: str = "") -> None:
        if self.color and style:
            text = f"{style}{text}{RESET}"
        print(text, file=self.out)

    def banner(self) -> None:
        for row in logo_rows(tick="\u2713" if self._can_print("\u2713") else "x", color=self.color):
            self.line(row, CYAN)
        self.line()
        self.line(f" {TAGLINE}", BOLD)
        self.line()

    def _can_print(self, text: str) -> bool:
        # Legacy Windows consoles (cp1252 etc.) raise UnicodeEncodeError on symbols like the tick.
        encoding = getattr(self.out, "encoding", None) or "utf-8"
        try:
            text.encode(encoding)
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def findings(self, report: PreflightReport) -> None:
        by_agent = {name: [] for name in AGENT_ORDER}
        for finding in report.findings:
            by_agent.setdefault(finding.agent, []).append(finding)

        for agent, findings in by_agent.items():
            decisions = [f for f in findings if f.payload is not None]
            notes = sorted((f for f in findings if f.payload is None), key=lambda f: (f.severity.rank, f.title))
            self.line()
            summary = f"{len(decisions)} decision{'s' if len(decisions) != 1 else ''}, {len(notes)} finding{'s' if len(notes) != 1 else ''}"
            self.line(f"[{agent}]  {summary}", BOLD)
            for finding in decisions:
                self.line(f"   +  {finding.title}", DIM)
            for finding in notes:
                self._finding(finding)

    def _finding(self, finding: Finding) -> None:
        tag = SEVERITY_TAGS[finding.severity]
        trap = f"{finding.trap_id} " if finding.trap_id else ""
        state = "" if not finding.mitigated or finding.severity is Severity.INFO else "  (guarded in spec)"
        self.line(f"   {tag}  {trap}{finding.title}{state}", SEVERITY_COLORS[finding.severity])
        if finding.severity is not Severity.INFO and finding.recommendations:
            self.line(f"         -> {finding.recommendations[0]}")

    def verdict(self, report: PreflightReport) -> None:
        self.line()
        self.line(f"Risk score: {report.risk_score}/100")
        text = VERDICT_TEXT[report.verdict]
        if report.verdict is Verdict.PASS and not report.warnings:
            text = f"PASS    no known traps matched ({len(TRAPS)} checked); the stack is a default, not a guarantee"
        self.line(f"Verdict:    {text}", BOLD + VERDICT_COLORS[report.verdict])

    def files(self, written, skipped) -> None:
        self.line()
        for path in written:
            self.line(f"   wrote    {path}", GREEN)
        for path in skipped:
            self.line(f"   skipped  {path} (already exists; use --force to overwrite)", YELLOW)
        if written:
            self.line()
            self.line("Open your AI assistant in this folder and start building. PROJECT.md is the source of truth.")


def logo_rows(tick: str = "\u2713", color: bool = False) -> List[str]:
    """The folded-page logo, one string per row. Widths are computed, so edges always line up."""
    w = LOGO_WIDTH

    def accent(text: str, style: str) -> str:
        # Rows are printed in CYAN; switch style for the text, then restore CYAN.
        return f"{style}{text}{RESET}{CYAN}" if color else text

    rows = [
        "       ." + "-" * w + ".",
        "      /" + " " * w + "/|",
        "     /" + accent(LOGO_TITLE.center(w), BOLD + WHITE) + "/ |",
        "    /" + "_" * w + "/  |",
        "    |" + " " * w + "|  |",
    ]
    right_edges = ["|  |"] * (len(LOGO_FEATURES) - 1) + ["|  /"]
    for feature, edge in zip(LOGO_FEATURES, right_edges):
        text = f"  [{tick}] {feature}"
        rows.append("    |" + accent(text, GREEN) + " " * (w - len(text)) + edge)
    rows += [
        "    |" + " " * w + "| /",
        "    |" + "_" * w + "|/",
    ]
    return rows


def _parse_targets(raw: Optional[str]) -> List[ContextTarget]:
    if not raw:
        return list(EXPORTERS)
    supported = {t.value: t for t in EXPORTERS}
    targets = []
    for name in (part.strip().lower() for part in raw.split(",") if part.strip()):
        if name not in supported:
            raise ValueError(f"unknown target '{name}'; choose from {', '.join(supported)}")
        targets.append(supported[name])
    return targets


def _supports_color(stream: TextIO) -> bool:
    if os.environ.get("NO_COLOR") or not hasattr(stream, "isatty") or not stream.isatty():
        return False
    # Legacy Windows consoles print raw escape codes; Windows Terminal and most modern shells don't.
    return os.name != "nt" or "WT_SESSION" in os.environ or "TERM" in os.environ


if __name__ == "__main__":
    sys.exit(main())
