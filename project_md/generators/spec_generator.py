"""Render a PreflightReport as PROJECT.md, the universal architecture spec."""

from __future__ import annotations

from project_md.core.knowledge_base import get_trap
from project_md.core.models import DataModel, PreflightReport, Severity, Verdict

VERDICT_BANNERS = {
    Verdict.PASS: "PASS: cleared for implementation.",
    Verdict.REVIEW: "REVIEW: a human must resolve the items under *Needs review* before implementation.",
    Verdict.BLOCK: "BLOCK: the idea as described commits to a known dead end. Follow the mandated replacements below.",
}

PYTHON_TYPES = {"uuid": "UUID", "str": "str", "int": "int", "float": "float", "bool": "bool", "datetime": "datetime"}
TS_TYPES = {"uuid": "string", "str": "string", "int": "number", "float": "number", "bool": "boolean", "datetime": "string"}


class SpecGenerator:
    """Renders PROJECT.md. Pure function of the report: same report, same bytes."""

    filename = "PROJECT.md"

    def render(self, report: PreflightReport) -> str:
        sections = [
            self._header(report),
            self._dead_ends(report),
            self._needs_review(report),
            self._stack(report),
            self._architecture(report),
            self._contracts(report),
            self._guidance(report),
        ]
        return "\n\n".join(s for s in sections if s) + "\n"

    def _header(self, report: PreflightReport) -> str:
        intent = report.intent
        lines = [
            "# PROJECT.md",
            "",
            f"> **Idea:** {intent.idea}",
            "",
            f"**Pre-flight verdict:** {VERDICT_BANNERS[report.verdict]}  ",
            f"**Risk score:** {report.risk_score}/100",
            "",
            f"- Platforms: {', '.join(p.value for p in intent.platforms)}",
            f"- Constraints: {', '.join(c.value for c in intent.constraints) or 'none detected'}",
            f"- Problem domains: {', '.join(c.value for c in intent.categories) or 'standard CRUD'}",
        ]
        return "\n".join(lines)

    def _dead_ends(self, report: PreflightReport) -> str:
        trap_findings = sorted(
            (f for f in report.findings if f.trap_id),
            key=lambda f: (f.severity.rank, f.trap_id),
        )
        if not trap_findings:
            return ""
        lines = ["## Dead ends: DO NOT build it this way", ""]
        for finding in trap_findings:
            trap = get_trap(finding.trap_id)
            marker = " (you asked for this)" if not finding.mitigated else ""
            lines += [
                f"### [{finding.severity.value.upper()}] {trap.id}: {trap.title}{marker}",
                f"- **DO NOT:** {trap.trap}",
                f"- **WHY:** {trap.why_it_fails}",
                f"- **USE INSTEAD:** {'; '.join(trap.recommended)}",
                "",
            ]
        return "\n".join(lines).rstrip()

    def _needs_review(self, report: PreflightReport) -> str:
        items = [f for f in report.findings if not f.mitigated and not f.trap_id and f.severity is not Severity.INFO]
        if not items:
            return ""
        lines = ["## Needs review", ""]
        for finding in items:
            lines.append(f"- **{finding.title}** ({finding.agent}): {finding.detail}")
            lines += [f"  - {r}" for r in finding.recommendations]
        return "\n".join(lines)

    def _stack(self, report: PreflightReport) -> str:
        lines = ["## Tech stack", "", "| Role | Choice | Why |", "| :--- | :--- | :--- |"]
        lines += [f"| {c.role} | {c.choice} | {c.rationale} |" for c in report.stack.components]
        return "\n".join(lines)

    def _architecture(self, report: PreflightReport) -> str:
        if not report.layers:
            return ""
        lines = ["## Architecture", "", "| Layer | Responsibility | May import |", "| :--- | :--- | :--- |"]
        lines += [f"| {l.name} | {l.responsibility} | {', '.join(l.may_depend_on) or 'nothing'} |" for l in report.layers]
        lines += ["", "Dependencies point inward only. Any import not listed above is a violation."]
        return "\n".join(lines)

    def _contracts(self, report: PreflightReport) -> str:
        if not report.data_models and not report.endpoints:
            return ""
        lines = ["## Data contracts"]
        if report.data_models:
            python = report.stack.language == "Python"
            lang = "python" if python else "typescript"
            render = self._pydantic if python else self._typescript
            lines += ["", f"```{lang}", "\n\n".join(render(m) for m in report.data_models), "```"]
        if report.endpoints:
            lines += ["", "### API", "", "| Method | Path | Purpose |", "| :--- | :--- | :--- |"]
            lines += [f"| {e.method} | `{e.path}` | {e.purpose} |" for e in report.endpoints]
        return "\n".join(lines)

    def _guidance(self, report: PreflightReport) -> str:
        items = [
            f for f in report.findings
            if f.payload is None and not f.trap_id and (f.mitigated or f.severity is Severity.INFO)
        ]
        if not items:
            return ""
        lines = ["## Rules for the AI assistant", ""]
        for finding in items:
            lines.append(f"- **{finding.title}:** {finding.detail}")
            lines += [f"  - {r}" for r in finding.recommendations]
        return "\n".join(lines)

    @staticmethod
    def _pydantic(model: DataModel) -> str:
        lines = [f"class {model.name}(BaseModel):", f'    """{model.description}"""']
        for f in model.fields:
            py = _map_type(f.type, PYTHON_TYPES, "list[{}]")
            lines.append(f"    {f.name}: {py} | None = None" if f.optional else f"    {f.name}: {py}")
        return "\n".join(lines)

    @staticmethod
    def _typescript(model: DataModel) -> str:
        lines = [f"/** {model.description} */", f"export interface {model.name} {{"]
        for f in model.fields:
            ts = _map_type(f.type, TS_TYPES, "{}[]")
            lines.append(f"  {f.name}{'?' if f.optional else ''}: {ts};")
        lines.append("}")
        return "\n".join(lines)


def _map_type(neutral: str, table: dict, list_format: str) -> str:
    if neutral.startswith("list[") and neutral.endswith("]"):
        return list_format.format(_map_type(neutral[5:-1], table, list_format))
    return table[neutral]
