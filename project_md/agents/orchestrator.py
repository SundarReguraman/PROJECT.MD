"""Orchestrator: runs the five specialists in parallel and reaches a verdict.

Scoring (0-100, capped):
    CRITICAL 40, WARNING 15, INFO 3 points per finding.
    Mitigated findings (the spec already mandates the fix) count 25%.
    Findings carrying a payload are decisions (stack, layers, contracts), not risks: 0.

Verdict:
    BLOCK   any unmitigated CRITICAL (the idea explicitly names a dead end)
    REVIEW  any unmitigated WARNING, or score >= REVIEW_THRESHOLD
    PASS    otherwise
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional, Sequence

from project_md.agents import default_agents
from project_md.agents.base_agent import BaseAgent
from project_md.core.intent import infer_intent
from project_md.core.knowledge_base import scan
from project_md.core.models import (
    ApiEndpoint,
    ArchitectureLayer,
    DataModel,
    Finding,
    PreflightReport,
    Severity,
    StackComponent,
    TechStack,
    Verdict,
)
from project_md.generators.spec_generator import SpecGenerator

WEIGHTS = {Severity.CRITICAL: 40, Severity.WARNING: 15, Severity.INFO: 3}
MITIGATED_FACTOR = 0.25
REVIEW_THRESHOLD = 50


@dataclass
class PreflightOutcome:
    report: PreflightReport
    project_md: str  # Rendered PROJECT.md


class Orchestrator:
    def __init__(self, agents: Optional[Sequence[BaseAgent]] = None, generator: Optional[SpecGenerator] = None):
        self.agents: List[BaseAgent] = list(agents) if agents is not None else default_agents()
        self.generator = generator or SpecGenerator()

    async def run(self, idea: str) -> PreflightOutcome:
        warnings = scan(idea)
        intent = infer_intent(idea, warnings)
        domain_context = {"intent": intent, "warnings": warnings}

        results = await asyncio.gather(
            *(agent.evaluate(idea, domain_context) for agent in self.agents),
            return_exceptions=True,
        )

        findings: List[Finding] = []
        for agent, result in zip(self.agents, results):
            if isinstance(result, BaseException):
                # One broken specialist must not sink the run, but its silence is not a clean bill of health.
                findings.append(
                    Finding(
                        agent=agent.name or type(agent).__name__,
                        severity=Severity.WARNING,
                        title=f"{agent.name or type(agent).__name__} agent failed",
                        detail=f"{type(result).__name__}: {result}. Its checks did not run.",
                    )
                )
            else:
                findings.extend(result)

        report = self._consolidate(intent, warnings, findings)
        return PreflightOutcome(report=report, project_md=self.generator.render(report))

    def run_sync(self, idea: str) -> PreflightOutcome:
        return asyncio.run(self.run(idea))

    @staticmethod
    def _consolidate(intent, warnings, findings: List[Finding]) -> PreflightReport:
        components = [f.payload for f in findings if isinstance(f.payload, StackComponent)]
        language = next((c.choice for c in components if c.role == "Language"), "")
        report = PreflightReport(
            intent=intent,
            stack=TechStack(language=language, components=components),
            warnings=warnings,
            layers=[f.payload for f in findings if isinstance(f.payload, ArchitectureLayer)],
            findings=findings,
            data_models=[f.payload for f in findings if isinstance(f.payload, DataModel)],
            endpoints=[f.payload for f in findings if isinstance(f.payload, ApiEndpoint)],
        )
        report.risk_score = risk_score(findings)
        report.verdict = verdict(findings, report.risk_score)
        return report


def risk_score(findings: List[Finding]) -> int:
    total = sum(
        WEIGHTS[f.severity] * (MITIGATED_FACTOR if f.mitigated else 1)
        for f in findings
        if f.payload is None
    )
    return min(100, round(total))


def verdict(findings: List[Finding], score: int) -> Verdict:
    open_findings = [f for f in findings if not f.mitigated]
    if any(f.severity is Severity.CRITICAL for f in open_findings):
        return Verdict.BLOCK
    if any(f.severity is Severity.WARNING for f in open_findings) or score >= REVIEW_THRESHOLD:
        return Verdict.REVIEW
    return Verdict.PASS
