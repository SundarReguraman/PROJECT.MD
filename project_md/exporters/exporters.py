"""Native context-file exporters, one per AI assistant.

Each exporter turns a PreflightReport into ``{relative path: file content}``.
Exporters never touch the disk; ``project_md.exporters.write_files`` does.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from project_md.core.models import ContextTarget, PreflightReport
from project_md.exporters.common import (
    commands,
    dead_ends,
    guidance,
    header_note,
    layer_rules,
    open_issues,
    stack_lines,
    typing_rule,
)
from project_md.generators.spec_generator import SpecGenerator


class Exporter(ABC):
    target: ContextTarget

    @abstractmethod
    def render(self, report: PreflightReport) -> Dict[str, str]:
        """Return ``{relative path: content}`` for this assistant."""


class ProjectExporter(Exporter):
    """PROJECT.md: the universal master spec every other file points to."""

    target = ContextTarget.PROJECT

    def __init__(self, generator: SpecGenerator = None):
        self.generator = generator or SpecGenerator()

    def render(self, report: PreflightReport) -> Dict[str, str]:
        return {self.generator.filename: self.generator.render(report)}


class ClaudeExporter(Exporter):
    """CLAUDE.md for Claude Code: commands, hard boundaries, idioms."""

    target = ContextTarget.CLAUDE

    def render(self, report: PreflightReport) -> Dict[str, str]:
        lines = [
            header_note("Claude Code"),
            "# CLAUDE.md",
            "",
            f"{report.intent.idea}",
            "",
            "Full spec, data contracts and API: `PROJECT.md`. Read it before starting any feature.",
            "",
            "## Commands",
            "",
        ]
        lines += [f"- {purpose}: `{cmd}`" for purpose, cmd in commands(report)]
        lines += ["", "## Stack (decided; do not substitute)", ""]
        lines += [f"- {line}" for line in stack_lines(report)]
        traps = dead_ends(report)
        if traps:
            lines += ["", "## NEVER", ""]
            lines += [f"- **{tid}: never use {what}.** {why} Use instead: {use}." for tid, what, why, use in traps]
        lines += ["", "## Architecture boundaries", ""]
        lines += [f"- {rule}" for rule in layer_rules(report)]
        lines += [
            "",
            "## Code style & errors",
            "",
            f"- {typing_rule(report)}",
            "- Raise domain-specific exceptions in Domain/Service; translate them to HTTP/UI errors only in Interface.",
            "- Never swallow exceptions silently; log with context and re-raise or return a typed error.",
        ]
        lines += [f"- {f.title}: {f.detail}" for f in guidance(report)]
        issues = open_issues(report)
        if issues:
            lines += ["", "## Unresolved: ask the user before building these parts", ""]
            lines += [f"- {f.title}: {f.detail}" for f in issues]
        return {self.target.filename: "\n".join(lines) + "\n"}


class CursorExporter(Exporter):
    """.cursorrules for Cursor: flat, imperative directives."""

    target = ContextTarget.CURSOR

    def render(self, report: PreflightReport) -> Dict[str, str]:
        lines = [
            f"You are building: {report.intent.idea}",
            "The architecture was pre-flighted. Follow PROJECT.md exactly; it is the source of truth.",
            "",
            "STACK (do not substitute or add alternatives):",
        ]
        lines += [f"- {line}" for line in stack_lines(report)]
        traps = dead_ends(report)
        if traps:
            lines += ["", "FORBIDDEN APPROACHES (known dead ends):"]
            lines += [f"- Do not use {what}. Use {use}. ({tid})" for tid, what, _, use in traps]
        lines += ["", "LAYER RULES:"]
        lines += [f"- {rule}" for rule in layer_rules(report)]
        lines += ["", "TYPING:", f"- {typing_rule(report)}"]
        if report.data_models:
            lines += ["- Implement these data models exactly as specified in PROJECT.md: " + ", ".join(m.name for m in report.data_models) + "."]
        lines += ["", "RULES:"]
        lines += [f"- {f.title}: {f.detail}" for f in guidance(report)]
        issues = open_issues(report)
        if issues:
            lines += ["", "STOP AND ASK THE USER BEFORE:"]
            lines += [f"- {f.title}: {f.detail}" for f in issues]
        return {self.target.filename: "\n".join(lines) + "\n"}


class GeminiExporter(Exporter):
    """GEMINI.md plus .agent/rules/*.md for Google Antigravity.

    GEMINI.md stays short and points to topic rule files (progressive disclosure),
    so the agent loads detail only when a task touches that topic.
    """

    target = ContextTarget.GEMINI
    rules_dir = ".agent/rules"

    def render(self, report: PreflightReport) -> Dict[str, str]:
        rules = self._rules(report)
        index = [
            header_note("Google Antigravity"),
            "# GEMINI.md",
            "",
            report.intent.idea,
            "",
            f"Pre-flight verdict: **{report.verdict.value.upper()}** (risk {report.risk_score}/100). Full spec: `PROJECT.md`.",
            "",
            "## Stack",
            "",
        ]
        index += [f"- {line}" for line in stack_lines(report)]
        index += ["", "## Workspace rules", "", "Load the matching rule file before working on that area:", ""]
        index += [f"- `{path}`: {title}" for path, (title, _) in rules.items()]
        index += [
            "",
            "## Subagent protocol",
            "",
            "- Before implementing, a planning subagent checks the task against `dead-ends.md` and `architecture.md`.",
            "- A subagent that finds a conflict stops and reports it; it never works around a rule silently.",
            "- Every change to a data model must update `contracts.md` and `PROJECT.md` in the same task.",
        ]
        files = {self.target.filename: "\n".join(index) + "\n"}
        for path, (title, body) in rules.items():
            files[path] = f"# {title}\n\n" + "\n".join(body) + "\n"
        return files

    def _rules(self, report: PreflightReport) -> Dict[str, tuple]:
        rules: Dict[str, tuple] = {}
        traps = dead_ends(report)
        if traps:
            body: List[str] = []
            for tid, what, why, use in traps:
                body += [f"## {tid}", f"- Do not: {what}", f"- Why: {why}", f"- Use instead: {use}", ""]
            rules[f"{self.rules_dir}/dead-ends.md"] = ("Dead ends: forbidden approaches", body)
        rules[f"{self.rules_dir}/architecture.md"] = (
            "Architecture layers",
            [f"- {rule}" for rule in layer_rules(report)] + ["", "Dependencies point inward only."],
        )
        if report.data_models or report.endpoints:
            body = [f"- {typing_rule(report)}", ""]
            body += [f"- {m.name}: " + ", ".join(f"{fld.name}: {fld.type}" for fld in m.fields) for m in report.data_models]
            if report.endpoints:
                body += [""] + [f"- `{e.method} {e.path}`: {e.purpose}" for e in report.endpoints]
            rules[f"{self.rules_dir}/contracts.md"] = ("Data contracts & API", body)
        security = [f for f in report.findings if f.agent == "security" and not f.trap_id]
        if security:
            body = []
            for f in security:
                body.append(f"- **{f.title}:** {f.detail}")
                body += [f"  - {r}" for r in f.recommendations]
            rules[f"{self.rules_dir}/security.md"] = ("Security & privacy", body)
        return rules


class AgentsExporter(Exporter):
    """AGENTS.md for IBM Bob / OpenCode, with per-mode operating constraints."""

    target = ContextTarget.AGENTS

    def render(self, report: PreflightReport) -> Dict[str, str]:
        lines = [
            header_note("IBM Bob / OpenCode"),
            "# AGENTS.md",
            "",
            report.intent.idea,
            "",
            "## Index first",
            "",
            "Index these before planning: `PROJECT.md` (spec and contracts), then the Domain and Service layers.",
            "",
            "## Setup & commands",
            "",
        ]
        lines += [f"- {purpose}: `{cmd}`" for purpose, cmd in commands(report)]
        lines += ["", "## Stack", ""]
        lines += [f"- {line}" for line in stack_lines(report)]
        lines += ["", "## Architecture", ""]
        lines += [f"- {rule}" for rule in layer_rules(report)]
        traps = dead_ends(report)
        if traps:
            lines += ["", "## Forbidden approaches", ""]
            lines += [f"- {tid}: do not use {what}. Use {use}." for tid, what, _, use in traps]
        lines += [
            "",
            "## Mode constraints",
            "",
            "- **Plan mode:** read-only. Check every proposed step against *Forbidden approaches* and *Architecture*; "
            "flag conflicts instead of planning around them.",
            "- **Code mode:** implement only what the approved plan covers. Keep contracts identical to `PROJECT.md`.",
            "- **Ask mode:** answer from `PROJECT.md` first; say so when the spec does not cover the question.",
            "",
            "## Code style",
            "",
            f"- {typing_rule(report)}",
        ]
        lines += [f"- {f.title}: {f.detail}" for f in guidance(report)]
        issues = open_issues(report)
        if issues:
            lines += ["", "## Needs a human decision", ""]
            lines += [f"- {f.title}: {f.detail}" for f in issues]
        lines += [
            "",
            "## Session summary",
            "",
            "At the end of each task, summarise: files changed, contracts touched, and any rule you could not follow and why.",
        ]
        return {self.target.filename: "\n".join(lines) + "\n"}


EXPORTERS: Dict[ContextTarget, Exporter] = {
    exporter.target: exporter
    for exporter in (ProjectExporter(), ClaudeExporter(), CursorExporter(), GeminiExporter(), AgentsExporter())
}


def render_all(report: PreflightReport, targets: List[ContextTarget] = None) -> Dict[str, str]:
    """Render every requested target (default: all supported) into one file map."""
    files: Dict[str, str] = {}
    for target in targets or list(EXPORTERS):
        files.update(EXPORTERS[target].render(report))
    return files
