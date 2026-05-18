"""
Structural disclaimer injector — ensures "not legal advice" is present
in every API response, generated document, and calendar entry.

This is code-level enforcement, not a README footnote.
Removing it requires editing this source file.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────
# The canonical disclaimer text
# ─────────────────────────────────────────────────────

DISCLAIMER_HUMAN = (
    "IMPORTANT: This system produces legal information and drafts, not legal advice. "
    "It is a tool for lawyers and informed business users, not a replacement for licensed counsel. "
    "All outputs should be reviewed by qualified legal professionals before any business decision "
    "is made based on them. This system does not practice law and does not establish an "
    "attorney-client relationship."
)

DISCLAIMER_SHORT = "NOT LEGAL ADVICE — For informational and drafting purposes only. Review by licensed counsel required."

# Machine-readable disclaimer key — present in every API response schema
DISCLAIMER_KEY = "_not_legal_advice_disclaimer"


class DisclaimerPayload(BaseModel):
    """Machine-readable disclaimer struct attached to every output."""

    disclaimer: str = Field(default=DISCLAIMER_HUMAN)
    short_disclaimer: str = Field(default=DISCLAIMER_SHORT)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    jurisdiction: str | None = Field(
        default=None,
        description="Jurisdiction this disclaimer applies to (if configured)",
    )


def inject_disclaimer(data: dict[str, Any]) -> dict[str, Any]:
    """Inject the machine-readable disclaimer into a response dict.

    Used by FastAPI middleware and every agent output serializer.
    """
    data[DISCLAIMER_KEY] = DisclaimerPayload().model_dump(mode="json")
    return data


def disclaimer_footer() -> str:
    """Human-readable disclaimer footer for documents and emails."""
    return f"\n\n{'─' * 60}\n{DISCLAIMER_HUMAN}\n{'─' * 60}\n"


def disclaimer_html() -> str:
    """HTML version of the disclaimer for web dashboard outputs."""
    return (
        '<div class="legal-disclaimer" style="'
        'border-top: 2px solid #ccc; padding: 12px; margin-top: 24px; '
        'font-size: 12px; color: #666; background: #f9f9f9;">'
        f"<strong>{DISCLAIMER_SHORT}</strong><br>{DISCLAIMER_HUMAN}</div>"
    )
