"""Infer a ProjectIntent from the user's single plain-English idea.

CLAUDE.md rule 2: never ask the beginner follow-up questions. Everything here
is inferred from the idea text with case-insensitive regexes.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from project_md.core.knowledge_base import scan
from project_md.core.models import Category, Constraint, Platform, ProjectIntent, TrapWarning

CONSTRAINT_PATTERNS: Dict[Constraint, Tuple[str, ...]] = {
    Constraint.OFFLINE: (r"\boffline\b", r"\bno internet\b", r"\bwithout (?:an? )?internet\b", r"\bon[- ]device\b", r"\blocal[- ]first\b", r"\bair[- ]gapped\b"),
    Constraint.LOW_BUDGET: (r"\bfree\b", r"\bcheap\w*\b", r"\blow[- ]cost\b", r"\bno (?:cloud )?costs?\b", r"\bbudget\b", r"\bstudents?\b", r"\bhackathon\b"),
    Constraint.LOW_LATENCY: (r"\bfast\b", r"\binstant\w*\b", r"\blow[- ]latency\b", r"\breal[- ]?time\b", r"\bunder \d+ ?(?:ms|milliseconds?|seconds?|s)\b", r"\b< ?\d+ ?(?:ms|s)\b"),
    Constraint.PRIVACY_SENSITIVE: (r"\bmedical\b", r"\bhealth\w*\b", r"\bpatients?\b", r"\bdoctors?'?s?\b", r"\bclinic\w*\b", r"\bhipaa\b", r"\btherap\w*\b", r"\bbank\w*\b", r"\bfinancial\b", r"\bchildren\b", r"\bkids\b", r"\bminors\b", r"\blegal\b", r"\bgdpr\b", r"\bpersonal data\b"),
    Constraint.HIGH_SCALE: (r"\bmillions?\b", r"\bat scale\b", r"\b(?:thousands|lots) of (?:concurrent )?users\b", r"\bviral\b", r"\bhigh[- ]traffic\b"),
}

PLATFORM_PATTERNS: Dict[Platform, Tuple[str, ...]] = {
    Platform.WEB: (r"\bweb\w*\b", r"\bsites?\b", r"\bbrowser\b", r"\bsaas\b", r"\bdashboard\b", r"\bportal\b"),
    Platform.MOBILE: (r"\bmobile\b", r"\bios\b", r"\bandroid\b", r"\biphone\b", r"\bphone app\b", r"\btablets?\b"),
    Platform.DESKTOP: (r"\bdesktop\b", r"\bmac ?os app\b", r"\bwindows app\b", r"\belectron\b", r"\btauri\b"),
    Platform.CLI: (r"\bcli\b", r"\bcommand[- ]line\b", r"\bterminal\b", r"\bscripts?\b"),
    Platform.API: (r"\bapis?\b", r"\bbackend\b", r"\bwebhooks?\b", r"\bmicroservices?\b"),
}

LANGUAGE_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("TypeScript", r"\btypescript\b|\bts\b"),
    ("JavaScript", r"\bjavascript\b|\bnode(?:\.?js)?\b"),
    ("Python", r"\bpython\b|\bdjango\b|\bflask\b|\bfastapi\b"),
    ("Go", r"\bgolang\b|\bgo (?:backend|service|lang)\b"),
    ("Rust", r"\brust\b"),
    ("Kotlin", r"\bkotlin\b"),
    ("Swift", r"\bswift\b|\bswiftui\b"),
    ("Java", r"\bjava\b"),
)


def infer_intent(idea: str, warnings: List[TrapWarning] = None) -> ProjectIntent:
    """Build a ProjectIntent from ``idea``. Pass ``warnings`` to reuse an existing scan."""
    if warnings is None:
        warnings = scan(idea)

    categories: List[Category] = []
    for warning in warnings:
        if warning.trap.category not in categories:
            categories.append(warning.trap.category)

    constraints = [c for c, patterns in CONSTRAINT_PATTERNS.items() if _any_match(patterns, idea)]
    platforms = [p for p, patterns in PLATFORM_PATTERNS.items() if _any_match(patterns, idea)]
    if not platforms:
        # "An app to ..." with no platform named: the web reaches every device.
        platforms = [Platform.WEB]

    language = next((name for name, pattern in LANGUAGE_PATTERNS if re.search(pattern, idea, re.IGNORECASE)), "")

    return ProjectIntent(
        idea=idea,
        categories=categories,
        constraints=constraints,
        platforms=platforms,
        language=language,
    )


def needs_backend(intent: ProjectIntent) -> bool:
    """False for offline apps and pure CLI/desktop tools, which call the Service layer in-process."""
    if Constraint.OFFLINE in intent.constraints:
        return False
    return not set(intent.platforms) <= {Platform.CLI, Platform.DESKTOP}


def _any_match(patterns: Tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
