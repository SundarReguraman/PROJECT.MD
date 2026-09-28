"""Impact agent: complexity, latency bottlenecks, scalability traps and constraint conflicts."""

from __future__ import annotations

from typing import List

from project_md.agents.base_agent import BaseAgent
from project_md.core.models import Category, Constraint, Finding, Severity, Trap

OWNED_CATEGORIES = frozenset({Category.REALTIME, Category.CONCURRENCY, Category.QUEUE, Category.DATABASE})
# Database traps that belong to other specialists.
NOT_OWNED = frozenset({"DB-003", "DB-004"})

HEAVY_INFERENCE = frozenset({Category.OCR, Category.COMPUTER_VISION, Category.AI_ML})
NEEDS_SERVER = frozenset({Category.REALTIME, Category.AUTH})

# Distinct problem domains above which an MVP is likely over-scoped.
SCOPE_LIMIT = 4


class ImpactAgent(BaseAgent):
    name = "impact"

    def owns(self, trap: Trap) -> bool:
        return trap.category in OWNED_CATEGORIES and trap.id not in NOT_OWNED

    async def evaluate(self, idea: str, domain_context: dict) -> List[Finding]:
        intent = self.intent(domain_context)
        categories = set(intent.categories)
        findings: List[Finding] = []

        count = len(categories)
        if count >= SCOPE_LIMIT:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.WARNING,
                    title=f"Scope risk: {count} hard problem domains",
                    detail=f"The idea spans {', '.join(sorted(c.value for c in categories))}. Each is a project on its own; "
                    "together they are the most common reason MVPs never ship.",
                    recommendations=("Pick the one flow that proves the idea and build only that first.",),
                )
            )
        else:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.INFO,
                    title=f"Complexity: {count} hard problem domain{'s' if count != 1 else ''}",
                    detail="Scope is manageable for an MVP." if count else "No specialised domains detected; a standard CRUD app.",
                    mitigated=True,
                )
            )

        if Constraint.OFFLINE in intent.constraints and categories & NEEDS_SERVER:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.WARNING,
                    title="Constraint conflict: offline vs server-dependent features",
                    detail=f"Offline was requested, but {', '.join(sorted(c.value for c in categories & NEEDS_SERVER))} "
                    "needs a server to be reachable.",
                    recommendations=(
                        "Go local-first: SQLite on device, sync when online (CRDTs for shared data)",
                        "Or drop the offline requirement for these features",
                    ),
                )
            )

        if Constraint.LOW_LATENCY in intent.constraints and categories & HEAVY_INFERENCE:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.WARNING,
                    title="Latency bottleneck: model inference",
                    detail="Model inference will dominate response time. CPU inference of a full-size model can take "
                    "seconds per item, which breaks a tight latency budget.",
                    recommendations=(
                        "Benchmark the chosen model on target hardware in week one",
                        "Use quantised/small variants via ONNX Runtime",
                    ),
                )
            )

        if Constraint.HIGH_SCALE in intent.constraints:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.INFO,
                    title="Scale expectation noted",
                    detail="Design for statelessness at the API tier so it can scale horizontally; keep state in the database.",
                    recommendations=("Don't pre-build for scale: measure first, then add caching or read replicas.",),
                    mitigated=True,
                )
            )

        findings.extend(self.trap_findings(domain_context))
        return findings
