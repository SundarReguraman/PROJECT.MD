"""Contract agent: synthesises data models and API endpoints for the idea."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from project_md.agents.base_agent import BaseAgent
from project_md.core.intent import needs_backend
from project_md.core.models import (
    ApiEndpoint,
    Category,
    DataField,
    DataModel,
    Finding,
    Severity,
    Trap,
)

F = DataField

USER = DataModel("User", "An account holder.", (
    F("id", "uuid"), F("email", "str"), F("display_name", "str", optional=True), F("created_at", "datetime"),
))

# (models, endpoints) per recognised domain. Money is always integer minor units (DB-003).
TEMPLATES: Dict[str, Tuple[Tuple[DataModel, ...], Tuple[ApiEndpoint, ...]]] = {
    "documents": (
        (
            DataModel("Document", "An uploaded image or scan awaiting recognition.", (
                F("id", "uuid"), F("owner_id", "uuid"), F("file_url", "str"), F("status", "str"), F("uploaded_at", "datetime"),
            )),
            DataModel("Transcription", "Recognised text for one document.", (
                F("id", "uuid"), F("document_id", "uuid"), F("text", "str"), F("confidence", "float"), F("created_at", "datetime"),
            )),
        ),
        (
            ApiEndpoint("POST", "/documents", "Upload an image/scan; returns a Document with status=pending."),
            ApiEndpoint("GET", "/documents/{id}", "Fetch a document and its processing status."),
            ApiEndpoint("GET", "/documents/{id}/transcription", "Fetch the recognised text."),
        ),
    ),
    "vision": (
        (
            DataModel("Image", "An image submitted for analysis.", (
                F("id", "uuid"), F("file_url", "str"), F("captured_at", "datetime"),
            )),
            DataModel("Detection", "One detected object in an image.", (
                F("id", "uuid"), F("image_id", "uuid"), F("label", "str"), F("confidence", "float"), F("bbox", "list[float]"),
            )),
        ),
        (
            ApiEndpoint("POST", "/images", "Submit an image for detection."),
            ApiEndpoint("GET", "/images/{id}/detections", "List detections for an image."),
        ),
    ),
    "chat": (
        (
            DataModel("Room", "A conversation channel.", (
                F("id", "uuid"), F("name", "str"), F("created_at", "datetime"),
            )),
            DataModel("Message", "One message in a room.", (
                F("id", "uuid"), F("room_id", "uuid"), F("author_id", "uuid"), F("body", "str"), F("sent_at", "datetime"),
            )),
        ),
        (
            ApiEndpoint("GET", "/rooms/{id}/messages", "Message history (paginated, newest first)."),
            ApiEndpoint("WS", "/ws/rooms/{id}", "Live message stream; clients send and receive Message events."),
        ),
    ),
    "collab": (
        (
            DataModel("SharedDoc", "A collaboratively edited document; content is a CRDT update log.", (
                F("id", "uuid"), F("title", "str"), F("owner_id", "uuid"), F("updated_at", "datetime"),
            )),
        ),
        (
            ApiEndpoint("POST", "/docs", "Create a shared document."),
            ApiEndpoint("WS", "/ws/docs/{id}", "CRDT sync channel (Yjs protocol)."),
        ),
    ),
    "commerce": (
        (
            DataModel("Product", "Something for sale. Prices are integer minor units (cents).", (
                F("id", "uuid"), F("name", "str"), F("price_cents", "int"), F("currency", "str"), F("stock", "int"),
            )),
            DataModel("Order", "A purchase. Totals are integer minor units (cents).", (
                F("id", "uuid"), F("buyer_id", "uuid"), F("total_cents", "int"), F("currency", "str"), F("status", "str"), F("created_at", "datetime"),
            )),
        ),
        (
            ApiEndpoint("GET", "/products", "List products."),
            ApiEndpoint("POST", "/orders", "Place an order (transactional: reserves stock and records payment intent)."),
            ApiEndpoint("GET", "/orders/{id}", "Order status."),
        ),
    ),
    "assistant": (
        (
            DataModel("Conversation", "A thread with the AI assistant.", (
                F("id", "uuid"), F("user_id", "uuid"), F("created_at", "datetime"),
            )),
            DataModel("Turn", "One user or assistant turn.", (
                F("id", "uuid"), F("conversation_id", "uuid"), F("role", "str"), F("content", "str"), F("created_at", "datetime"),
            )),
        ),
        (
            ApiEndpoint("POST", "/conversations", "Start a conversation."),
            ApiEndpoint("POST", "/conversations/{id}/turns", "Send a message; streams the assistant reply (SSE)."),
        ),
    ),
    "generic": (
        (
            DataModel("Item", "The core record of the app. Rename to your domain noun.", (
                F("id", "uuid"), F("title", "str"), F("notes", "str", optional=True), F("created_at", "datetime"), F("updated_at", "datetime"),
            )),
        ),
        (
            ApiEndpoint("GET", "/items", "List items."),
            ApiEndpoint("POST", "/items", "Create an item."),
            ApiEndpoint("PATCH", "/items/{id}", "Update an item."),
            ApiEndpoint("DELETE", "/items/{id}", "Delete an item."),
        ),
    ),
}

COMMERCE_TRAPS = frozenset({"DB-002", "DB-003"})


class ContractAgent(BaseAgent):
    name = "contract"

    def owns(self, trap: Trap) -> bool:
        return trap.id == "DB-003"  # Money types are a contract decision.

    async def evaluate(self, idea: str, domain_context: dict) -> List[Finding]:
        intent = self.intent(domain_context)
        trap_ids = {w.trap.id for w in domain_context["warnings"]}

        domains = self._domains(idea, intent.categories, trap_ids)
        models: List[DataModel] = []
        endpoints: List[ApiEndpoint] = []
        needs_accounts = Category.AUTH in intent.categories or any(d in domains for d in ("chat", "collab", "commerce", "assistant"))
        if needs_accounts:
            models.append(USER)
        for domain in domains:
            domain_models, domain_endpoints = TEMPLATES[domain]
            models.extend(m for m in domain_models if m not in models)
            endpoints.extend(domain_endpoints)
        if needs_backend(intent):
            endpoints.insert(0, ApiEndpoint("GET", "/health", "Liveness check for deploys and uptime monitors."))
        else:
            endpoints = []  # No server: the Interface calls Services in-process.

        findings = [
            Finding(self.name, Severity.INFO, f"Model: {m.name}", m.description, mitigated=True, payload=m)
            for m in models
        ]
        findings.extend(
            Finding(self.name, Severity.INFO, f"Endpoint: {e.method} {e.path}", e.purpose, mitigated=True, payload=e)
            for e in endpoints
        )
        findings.append(
            Finding(
                agent=self.name,
                severity=Severity.INFO,
                title="Contracts are the source of truth",
                detail="Validate every request and response at the Interface boundary against these models; never pass raw dicts inward.",
                recommendations=("Python: Pydantic models", "TypeScript: Zod schemas with inferred types"),
                mitigated=True,
            )
        )
        findings.extend(self.trap_findings(domain_context))
        return findings

    @staticmethod
    def _domains(idea: str, categories: List[Category], trap_ids: set) -> List[str]:
        domains = []
        if Category.OCR in categories:
            domains.append("documents")
        if Category.COMPUTER_VISION in categories:
            domains.append("vision")
        if "RT-002" in trap_ids:
            domains.append("collab")
        elif Category.REALTIME in categories and re.search(r"\bchat\w*\b|\bmessag\w*\b", idea, re.IGNORECASE):
            domains.append("chat")
        if trap_ids & COMMERCE_TRAPS:
            domains.append("commerce")
        if Category.AI_ML in categories and re.search(r"\bchat ?bot\b|\bassistant\b|\bchat with\b|\bask questions?\b", idea, re.IGNORECASE):
            domains.append("assistant")
        return domains or ["generic"]
