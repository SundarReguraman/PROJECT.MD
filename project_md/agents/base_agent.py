"""Base class for the specialist pre-flight agents.

Every agent receives the same ``domain_context`` built once by the
orchestrator, so agents never re-scan the idea or depend on each other and
can safely run in parallel:

    {
        "intent":   ProjectIntent,        # inferred categories, constraints, platforms
        "warnings": List[TrapWarning],    # knowledge-base scan of the idea
    }

Each trap in the knowledge base is owned by exactly one agent (see ``owns``),
so a trap is reported once, by the specialist best placed to explain it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from project_md.core.models import Finding, ProjectIntent, Trap, TrapWarning


class BaseAgent(ABC):
    #: Short identifier stamped on every finding this agent produces.
    name: str = ""

    @abstractmethod
    async def evaluate(self, idea: str, domain_context: dict) -> List[Finding]:
        """Return this agent's findings for ``idea``. Must not raise for normal input."""

    def owns(self, trap: Trap) -> bool:
        """Whether this agent reports ``trap``. Override in subclasses."""
        return False

    def trap_findings(self, domain_context: dict) -> List[Finding]:
        """Turn the owned trap warnings in ``domain_context`` into findings.

        A proactive warning (idea is merely in the trap's domain) is mitigated:
        the spec mandates the replacement. Explicitly naming the anti-pattern is
        not: the user has committed to the dead end.
        """
        warnings: List[TrapWarning] = domain_context["warnings"]
        return [
            Finding(
                agent=self.name,
                severity=warning.severity,
                title=warning.trap.title,
                detail=warning.trap.why_it_fails,
                recommendations=warning.trap.recommended,
                trap_id=warning.trap.id,
                mitigated=not warning.explicitly_mentioned,
            )
            for warning in warnings
            if self.owns(warning.trap)
        ]

    @staticmethod
    def intent(domain_context: dict) -> ProjectIntent:
        return domain_context["intent"]
