"""Core data models for the PROJECT.MD pre-flight pipeline.

Pipeline shape (one user input, everything else inferred):

    idea (str) -> ProjectIntent + [TrapWarning]
               -> 5 specialist agents (in parallel) -> [Finding]
               -> PreflightReport (risk score + verdict) -> exporters (PROJECT.md, ...)

Standard library only: dataclasses + enums, serialisable via ``to_dict()``.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class Severity(str, Enum):
    """How badly a trap hurts if the user walks into it."""

    CRITICAL = "critical"  # Dead end: the approach will not work; a rewrite is certain.
    WARNING = "warning"  # Works in a demo, collapses under real users or data.
    INFO = "info"  # Over-engineering or a cheaper/simpler path exists.

    @property
    def rank(self) -> int:
        return {"critical": 0, "warning": 1, "info": 2}[self.value]


class Category(str, Enum):
    """Problem domains the knowledge base covers."""

    OCR = "ocr"
    COMPUTER_VISION = "computer_vision"
    AUTH = "auth"
    DATABASE = "database"
    QUEUE = "queue"
    CONCURRENCY = "concurrency"
    REALTIME = "realtime"
    AI_ML = "ai_ml"
    SEARCH = "search"
    SCRAPING = "scraping"
    GEOLOCATION = "geolocation"
    PAYMENTS = "payments"
    NOTIFICATIONS = "notifications"


class Constraint(str, Enum):
    """Non-functional constraints inferred from the idea text."""

    OFFLINE = "offline"
    LOW_BUDGET = "low_budget"
    LOW_LATENCY = "low_latency"
    PRIVACY_SENSITIVE = "privacy_sensitive"
    HIGH_SCALE = "high_scale"


class Platform(str, Enum):
    """Delivery surfaces inferred from the idea text."""

    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    CLI = "cli"
    API = "api"


class ContextTarget(str, Enum):
    """AI assistant context files the exporters can generate."""

    PROJECT = "project"
    CLAUDE = "claude"
    GEMINI = "gemini"
    AGENTS = "agents"
    CURSOR = "cursor"
    COPILOT = "copilot"

    @property
    def filename(self) -> str:
        return {
            "project": "PROJECT.md",
            "claude": "CLAUDE.md",
            "gemini": "GEMINI.md",
            "agents": "AGENTS.md",
            "cursor": ".cursorrules",
            "copilot": ".github/copilot-instructions.md",
        }[self.value]


@dataclass(frozen=True)
class Trap:
    """A known architectural dead end and its modern replacement.

    ``idea_patterns`` fire when the idea is *in the trap's domain* (e.g. it
    mentions handwriting), so we warn before the user ever picks a library.
    ``anti_patterns`` are checked only once the domain matches; if the idea
    *explicitly names* the bad approach (e.g. "OpenCV"), the warning escalates
    to CRITICAL.
    Patterns are case-insensitive regular expressions.
    """

    id: str
    category: Category
    severity: Severity
    title: str
    idea_patterns: Tuple[str, ...]
    anti_patterns: Tuple[str, ...]
    trap: str
    why_it_fails: str
    recommended: Tuple[str, ...]

    def idea_matches(self, text: str) -> List[str]:
        """Return the domain terms from ``text`` that put it in this trap's domain."""
        return _find_all(self.idea_patterns, text)

    def anti_pattern_matches(self, text: str) -> List[str]:
        """Return the anti-pattern terms ``text`` explicitly chooses.

        Negated mentions ("I will NOT use OpenCV", "without Tesseract") are
        ignored: rejecting a dead end must never count as choosing it.
        """
        return _find_all(self.anti_patterns, text, skip_negated=True)


@dataclass(frozen=True)
class TrapWarning:
    """A trap that fired for a specific idea, with the evidence that fired it."""

    trap: Trap
    matched_terms: Tuple[str, ...]
    anti_pattern_terms: Tuple[str, ...] = ()

    @property
    def explicitly_mentioned(self) -> bool:
        """True when the user already named the bad approach in their idea."""
        return bool(self.anti_pattern_terms)

    @property
    def severity(self) -> Severity:
        # Naming the anti-pattern means they are about to walk into it: escalate.
        return Severity.CRITICAL if self.explicitly_mentioned else self.trap.severity


@dataclass
class ProjectIntent:
    """Everything the engine infers from the user's single plain-English input."""

    idea: str
    categories: List[Category] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    platforms: List[Platform] = field(default_factory=list)
    language: str = ""  # Language the user asked for, if any; empty means "engine decides".


@dataclass(frozen=True)
class StackComponent:
    """One chosen technology and why it was chosen."""

    role: str  # e.g. "Frontend", "Database", "Handwriting OCR"
    choice: str  # e.g. "Next.js", "SQLite", "TrOCR via ONNX Runtime"
    rationale: str


@dataclass
class TechStack:
    """The inferred stack, ordered roughly from user-facing to infrastructure."""

    language: str
    components: List[StackComponent] = field(default_factory=list)

    def get(self, role: str) -> StackComponent | None:
        for component in self.components:
            if component.role.lower() == role.lower():
                return component
        return None


@dataclass(frozen=True)
class ArchitectureLayer:
    """A clean-architecture layer and the layers it is allowed to import."""

    name: str
    responsibility: str
    may_depend_on: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DataField:
    """A field in a synthesised data contract. ``type`` is language-neutral:
    uuid, str, int, float, bool, datetime, or list[<type>]."""

    name: str
    type: str
    optional: bool = False


@dataclass(frozen=True)
class DataModel:
    """A synthesised entity, rendered as Pydantic or TypeScript by the exporters."""

    name: str
    description: str
    fields: Tuple[DataField, ...]


@dataclass(frozen=True)
class ApiEndpoint:
    method: str  # GET, POST, PATCH, DELETE, or WS
    path: str
    purpose: str


class Verdict(str, Enum):
    """The orchestrator's final call on the idea as described."""

    PASS = "pass"  # Safe to hand the spec to an AI assistant.
    REVIEW = "review"  # A human must decide something first (privacy, licence, conflict).
    BLOCK = "block"  # The idea explicitly commits to a known dead end.


# Structured output an agent attaches to a finding; the orchestrator files it
# into the matching report section.
FindingPayload = Union[StackComponent, ArchitectureLayer, DataModel, ApiEndpoint]


@dataclass(frozen=True)
class Finding:
    """One observation from one specialist agent.

    ``mitigated`` means the generated spec already bakes in the fix (e.g. a
    proactive trap warning whose replacement is mandated), so it counts for
    less in the risk score and can never block on its own.
    """

    agent: str
    severity: Severity
    title: str
    detail: str
    recommendations: Tuple[str, ...] = ()
    trap_id: str = ""
    mitigated: bool = False
    payload: Optional[FindingPayload] = None


@dataclass
class PreflightReport:
    """The full pre-flight result; the single input to every exporter."""

    intent: ProjectIntent
    stack: TechStack
    warnings: List[TrapWarning] = field(default_factory=list)
    layers: List[ArchitectureLayer] = field(default_factory=list)
    targets: List[ContextTarget] = field(default_factory=lambda: list(ContextTarget))
    findings: List[Finding] = field(default_factory=list)
    data_models: List[DataModel] = field(default_factory=list)
    endpoints: List[ApiEndpoint] = field(default_factory=list)
    risk_score: int = 0  # 0-100
    verdict: Verdict = Verdict.PASS

    @property
    def has_critical(self) -> bool:
        return any(w.severity is Severity.CRITICAL for w in self.warnings)

    def sorted_warnings(self) -> List[TrapWarning]:
        """Warnings ordered most severe first, then by trap id for stable output."""
        return sorted(self.warnings, key=lambda w: (w.severity.rank, w.trap.id))

    def to_dict(self) -> Dict[str, Any]:
        """JSON-safe dict (enums become their string values)."""
        data = asdict(self, dict_factory=_json_safe_dict)
        # Derived properties are not dataclass fields; add the ones consumers need.
        for raw, warning in zip(data["warnings"], self.warnings):
            raw["severity"] = warning.severity.value
            raw["explicitly_mentioned"] = warning.explicitly_mentioned
        data["has_critical"] = self.has_critical
        return data


# A negator followed by at most three words, ending right where a match starts.
# Words can't span punctuation, so "I'm not sure, maybe OpenCV" is not negated,
# and the three-word limit keeps "no idea how to use OpenCV" as a real choice.
_NEGATED_PREFIX = re.compile(
    r"\b(?:not|never|no|nor|without|avoid(?:ing)?|instead of|rather than|stop using|"
    r"(?:do|does|did|wo|would|should|ca|could|must)n['\u2019]?t)"
    r"(?:\s+[\w'\u2019-]+){0,3}\s*$",
    re.IGNORECASE,
)


def is_negated(text: str, start: int) -> bool:
    """Whether the match beginning at ``start`` sits inside a negation."""
    return bool(_NEGATED_PREFIX.search(text[:start]))


def _find_all(patterns: Tuple[str, ...], text: str, skip_negated: bool = False) -> List[str]:
    found: List[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if skip_negated and is_negated(text, match.start()):
                continue
            if match.group(0) not in found:
                found.append(match.group(0))
            break
    return found


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _json_safe_dict(items: List[Tuple[str, Any]]) -> Dict[str, Any]:
    return {key: _json_safe(value) for key, value in items}
