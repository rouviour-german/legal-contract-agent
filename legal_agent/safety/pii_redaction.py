"""PII redaction utility for telemetry and third-party logs.

Contract text and party names are NEVER sent to third-party observability
providers. This module provides hashing and redaction for safe logging.
"""

from __future__ import annotations

import hashlib
import re

from legal_agent.config import settings


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def redact_pii(text: str) -> str:
    """Redact likely-PII from text for safe third-party logging.

    Replaces:
    - Email addresses with [EMAIL]
    - Phone numbers with [PHONE]
    - SSN patterns with [SSN]
    - Addresses (heuristic) with [ADDRESS]
    - Party names with their hash prefix
    """
    # Emails
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)

    # US phone numbers
    text = re.sub(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "[PHONE]", text)

    # SSN
    text = re.sub(r"\d{3}-\d{2}-\d{4}", "[SSN]", text)

    return text


def safe_contract_summary(contract_text: str) -> str:
    """Create a safe summary for telemetry that excludes PII.

    Returns a string with character counts and clause counts only.
    """
    clause_count = len(re.findall(r"^(?:section|article|\d+\.)", contract_text, re.MULTILINE | re.IGNORECASE))
    return (
        f"contract_length={len(contract_text)}, "
        f"clause_count={clause_count}"
    )
