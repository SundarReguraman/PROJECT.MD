"""Security agent: authentication boundaries, secret management and data privacy."""

from __future__ import annotations

from typing import List

from project_md.agents.base_agent import BaseAgent
from project_md.core.models import Category, Constraint, Finding, Platform, Severity, Trap

# Domains that usually mean calling a paid third-party API with a secret key.
EXTERNAL_API = frozenset({Category.AI_ML, Category.OCR, Category.COMPUTER_VISION, Category.AUTH})


class SecurityAgent(BaseAgent):
    name = "security"

    def owns(self, trap: Trap) -> bool:
        return trap.category is Category.AUTH

    async def evaluate(self, idea: str, domain_context: dict) -> List[Finding]:
        intent = self.intent(domain_context)
        categories = set(intent.categories)
        offline = Constraint.OFFLINE in intent.constraints

        findings = [
            Finding(
                agent=self.name,
                severity=Severity.INFO,
                title="Secrets stay out of code",
                detail="API keys, database URLs and signing secrets live in environment variables, loaded from a "
                ".env file that is listed in .gitignore.",
                recommendations=("Commit a .env.example with placeholder values", "Rotate any key that is ever committed"),
                mitigated=True,
            )
        ]

        client_apps = {Platform.MOBILE, Platform.DESKTOP} & set(intent.platforms)
        if client_apps and categories & EXTERNAL_API and not offline:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.WARNING,
                    title="Never ship API keys inside client apps",
                    detail=f"Anything bundled in a {'/'.join(sorted(p.value for p in client_apps))} app can be extracted "
                    "in minutes. A leaked AI/OCR key is a surprise bill.",
                    recommendations=("Proxy third-party calls through your backend, which holds the key",),
                    mitigated=True,
                )
            )

        if Category.AUTH in categories:
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.INFO,
                    title="Authorisation at the Service layer",
                    detail="Every Service method checks the caller owns the record it touches. Hiding a button in the UI "
                    "is not access control.",
                    mitigated=True,
                )
            )

        if Constraint.PRIVACY_SENSITIVE in intent.constraints:
            egress = "" if offline else (
                " Sending this data to a third-party cloud API makes that vendor a data processor; "
                "prefer on-device processing or a vendor that signs a BAA/DPA."
            )
            findings.append(
                Finding(
                    agent=self.name,
                    severity=Severity.WARNING,
                    title="Sensitive personal data",
                    detail="The idea involves health, financial, legal or children's data, which is regulated "
                    "(HIPAA, GDPR, COPPA and similar). A human must confirm which rules apply before launch." + egress,
                    recommendations=(
                        "Encrypt at rest and in transit",
                        "Collect the minimum; set a retention period and delete after it",
                        "Log access to sensitive records",
                    ),
                )
            )

        findings.extend(self.trap_findings(domain_context))
        return findings
