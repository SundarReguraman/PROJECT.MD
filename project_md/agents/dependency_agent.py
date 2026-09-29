"""Dependency agent: picks the tech stack, flags fatal library traps and licence risks."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from project_md.agents.base_agent import BaseAgent
from project_md.core.intent import needs_backend
from project_md.core.models import (
    Category,
    Finding,
    Platform,
    ProjectIntent,
    Severity,
    StackComponent,
    Trap,
    TrapWarning,
)

# Library-choice traps. Other categories are owned by the agent whose concern they are.
OWNED_CATEGORIES = frozenset(
    {Category.OCR, Category.COMPUTER_VISION, Category.AI_ML, Category.SEARCH, Category.SCRAPING}
)

# Categories that make Python the natural default language (ecosystem lives there).
PYTHON_FIRST = frozenset({Category.OCR, Category.COMPUTER_VISION, Category.AI_ML, Category.SCRAPING})

CATEGORY_ROLES: Dict[Category, str] = {
    Category.OCR: "OCR",
    Category.COMPUTER_VISION: "Computer vision",
    Category.AUTH: "Authentication",
    Category.QUEUE: "Background jobs",
    Category.CONCURRENCY: "Concurrency",
    Category.REALTIME: "Real-time",
    Category.AI_ML: "AI / ML",
    Category.SEARCH: "Search",
    Category.SCRAPING: "Data collection",
    Category.GEOLOCATION: "Location & maps",
    Category.PAYMENTS: "Payments",
    Category.NOTIFICATIONS: "Push notifications",
}

# Traps whose first recommendation is advice rather than a technology.
STACK_CHOICE_OVERRIDES: Dict[str, str] = {
    "QUEUE-001": "Background worker queue (RQ/Dramatiq on Python, BullMQ on Node)",
    "AI-003": "RAG pipeline: chunk, embed, retrieve top-k, then prompt",
    "SCRAPE-001": "Official API / JSON endpoints first, Playwright where a browser is required",
    "GEO-001": "expo-location background tracking (distance-throttled) + WebSockets / Supabase Realtime",
    "PAY-001": "Stripe (Checkout for payments, Connect Express for marketplace payouts)",
}

# (pattern, licence, why it matters). Matched against the idea and chosen stack.
LICENSE_WATCHLIST: Tuple[Tuple[str, str, str], ...] = (
    (r"\bultralytics\b|\byolo\s?v?(?:5|8|11)?\b", "AGPL-3.0",
     "Ultralytics YOLO is AGPL-3.0: shipping it in a closed-source or hosted product requires "
     "open-sourcing your app or buying an Enterprise licence."),
    (r"\bmongo\w*\b", "SSPL",
     "Self-hosting MongoDB is fine, but offering it as a service triggers the SSPL; check before building a hosted product."),
    (r"\bpyqt\w*\b", "GPL-3.0 / commercial",
     "PyQt is GPL-3.0 unless you buy a commercial licence; PySide6 (LGPL) is the permissive alternative."),
    (r"\bitext\w*\b", "AGPL-3.0",
     "iText is AGPL-3.0; use pypdf/pdfplumber or buy a licence for closed-source use."),
)


class DependencyAgent(BaseAgent):
    name = "dependency"

    def owns(self, trap: Trap) -> bool:
        return trap.category in OWNED_CATEGORIES

    async def evaluate(self, idea: str, domain_context: dict) -> List[Finding]:
        intent = self.intent(domain_context)
        warnings: List[TrapWarning] = domain_context["warnings"]

        stack = self._choose_stack(intent, warnings)
        findings = [
            Finding(
                agent=self.name,
                severity=Severity.INFO,
                title=f"{component.role}: {component.choice}",
                detail=component.rationale,
                mitigated=True,
                payload=component,
            )
            for component in stack
        ]
        findings.extend(self.trap_findings(domain_context))
        findings.extend(self._license_findings(idea, stack))
        return findings

    def _choose_stack(self, intent: ProjectIntent, warnings: List[TrapWarning]) -> List[StackComponent]:
        backend = needs_backend(intent)
        # Python only where it can actually run: on a server, or as a CLI. It can't ship inside
        # React Native or Tauri apps, and ONNX Runtime has JS bindings for on-device models.
        python_fits = backend or intent.platforms == [Platform.CLI]
        language = intent.language or ("Python" if python_fits and PYTHON_FIRST & set(intent.categories) or intent.platforms == [Platform.CLI] else "TypeScript")

        stack = [
            StackComponent(
                "Language",
                language,
                "Requested in the idea." if intent.language else
                "Best library ecosystem for this problem domain." if language == "Python" else
                "One language across frontend and backend keeps a small team fast.",
            )
        ]
        stack.extend(self._interface_components(intent, language))
        if backend:
            server = "FastAPI" if language == "Python" else "Node.js + Fastify"
            stack.append(StackComponent("Backend API", server, "Typed, async, minimal boilerplate; generates OpenAPI docs."))
            stack.append(StackComponent("Database", "PostgreSQL (Supabase or Neon)", "Relational integrity, transactions, and a free managed tier."))
        else:
            stack.append(StackComponent("Database", "SQLite", "Zero-setup, single file, works offline and on-device."))

        seen_traps = set()
        for warning in warnings:
            trap = warning.trap
            if trap.category not in CATEGORY_ROLES or trap.id in seen_traps:
                continue
            seen_traps.add(trap.id)
            choice = STACK_CHOICE_OVERRIDES.get(trap.id, trap.recommended[0])
            stack.append(StackComponent(CATEGORY_ROLES[trap.category], choice, f"Mandated to avoid {trap.id}: {trap.title}."))
        return stack

    @staticmethod
    def _interface_components(intent: ProjectIntent, language: str) -> List[StackComponent]:
        components = []
        if Platform.WEB in intent.platforms:
            components.append(StackComponent("Web frontend", "Next.js (React) + Tailwind CSS", "Largest ecosystem; deploys free on Vercel."))
        if Platform.MOBILE in intent.platforms:
            components.append(StackComponent("Mobile app", "React Native (Expo)", "One codebase for iOS and Android; no Xcode needed to start."))
        if Platform.DESKTOP in intent.platforms:
            components.append(StackComponent("Desktop app", "Tauri", "Native-size installers (~10 MB) instead of Electron's ~150 MB."))
        if Platform.CLI in intent.platforms:
            cli = "argparse (standard library)" if language == "Python" else "commander"
            components.append(StackComponent("CLI", cli, "No extra dependencies for argument parsing."))
        return components

    def _license_findings(self, idea: str, stack: List[StackComponent]) -> List[Finding]:
        haystack = " ".join([idea] + [component.choice for component in stack])
        return [
            Finding(
                agent=self.name,
                severity=Severity.WARNING,
                title=f"Licence risk: {licence}",
                detail=why,
                recommendations=("Confirm the licence fits how you will distribute the product before building on it.",),
            )
            for pattern, licence, why in LICENSE_WATCHLIST
            if re.search(pattern, haystack, re.IGNORECASE)
        ]
