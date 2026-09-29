"""Architecture agent: defines clean-architecture layers and forbids cross-layer leaks."""

from __future__ import annotations

from typing import List

from project_md.agents.base_agent import BaseAgent
from project_md.core.intent import needs_backend
from project_md.core.models import ArchitectureLayer, Category, Finding, Severity, Trap

LAYERS = (
    ArchitectureLayer("Domain", "Entities, value objects and business rules. Pure code: no I/O, no frameworks."),
    ArchitectureLayer("Data", "Database access, file storage and adapters for external engines (OCR, ML, APIs).", ("Domain",)),
    ArchitectureLayer("Service", "Use cases that orchestrate Domain rules and Data adapters.", ("Domain", "Data")),
    ArchitectureLayer("Interface", "HTTP routes, UI, CLI and WebSocket handlers. Validates input, calls Services.", ("Service",)),
)

# External engines that must sit behind an adapter so they can be swapped.
ENGINE_CATEGORIES = frozenset(
    {Category.OCR, Category.COMPUTER_VISION, Category.AI_ML, Category.SEARCH, Category.SCRAPING}
)


class ArchitectureAgent(BaseAgent):
    name = "architecture"

    def owns(self, trap: Trap) -> bool:
        return trap.id == "DB-004"  # Microservices for an MVP is a structural decision.

    async def evaluate(self, idea: str, domain_context: dict) -> List[Finding]:
        intent = self.intent(domain_context)
        findings = [
            Finding(
                agent=self.name,
                severity=Severity.INFO,
                title=f"Layer: {layer.name}",
                detail=layer.responsibility,
                recommendations=(f"May import only: {', '.join(layer.may_depend_on) or 'nothing (innermost layer)'}.",),
                mitigated=True,
                payload=layer,
            )
            for layer in LAYERS
        ]
        findings.append(
            Finding(
                agent=self.name,
                severity=Severity.INFO,
                title="Forbidden cross-layer imports",
                detail="Dependencies point inward only. Interface never touches Data directly; Domain never imports a framework or driver.",
                recommendations=(
                    "Interface -> Data: FORBIDDEN (go through a Service)",
                    "Domain -> Service/Data/Interface: FORBIDDEN",
                    "Data -> Service/Interface: FORBIDDEN",
                ),
                mitigated=True,
            )
        )

        engines = [c.value for c in intent.categories if c in ENGINE_CATEGORIES]
        if engines:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.INFO,
                    title="Isolate external engines behind a port",
                    detail=f"The {', '.join(engines)} engine is the part most likely to be swapped. Define an interface "
                    "(e.g. `Recognizer.recognize(image) -> Transcription`) in Domain and implement it in Data.",
                    recommendations=("Swapping engines must not touch Service or Interface code.",),
                    mitigated=True,
                )
            )

        if len(intent.platforms) > 1:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.INFO,
                    title="One core, thin clients",
                    detail=f"Targets {', '.join(p.value for p in intent.platforms)}. Keep all business logic in the "
                    "shared Service layer; each platform is a thin Interface over "
                    + ("the same API." if needs_backend(intent) else "the same in-process Services."),
                    mitigated=True,
                )
            )

        findings.extend(self.trap_findings(domain_context))
        return findings
