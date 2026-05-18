"""
Immutable JSONL audit log writer.

Every decision made by any agent is logged here with:
- Timestamp
- Agent name
- Contract fingerprint (not full text)
- Input summary (hashed PII)
- Output summary
- HITL status
- Model/provider used
- Token/cost estimate

This log is append-only and is the canonical record for compliance,
debugging, and replay. It never contains full contract text.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from legal_agent.config import settings

logger = structlog.get_logger(__name__)


def _hash_pii(value: str, salt: str = "legal-agent-audit") -> str:
    """Hash a PII string for audit logging.

    Uses SHA-256 with a salt. Reversible only by brute force.
    The salt is NOT secret — the goal is preventing casual PII exposure,
    not cryptographic anonymization.
    """
    data = f"{salt}:{value}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:16]


def _sanitize_for_log(data: Any, max_str_len: int = 200) -> Any:
    """Recursively truncate long strings and hash likely-PII values."""
    if isinstance(data, str):
        if len(data) > max_str_len:
            return data[:max_str_len] + f"... [{len(data)} chars total]"
        return data
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            # Hash fields that look like names/addresses
            if k.lower() in ("name", "address", "signatory_name", "email", "phone"):
                result[k] = _hash_pii(str(v)) if v else v
            else:
                result[k] = _sanitize_for_log(v, max_str_len)
        return result
    if isinstance(data, list):
        return [_sanitize_for_log(item, max_str_len) for item in data]
    return data


class AuditLogWriter:
    """Append-only JSONL audit log.

    Thread-safe and process-safe via O_APPEND on the file descriptor.
    Writes to a daily-rotated file in the configured output directory.
    """

    def __init__(self, log_dir: Path | None = None) -> None:
        self._log_dir = log_dir or settings.output_dir / "audit"
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _current_file(self) -> Path:
        """Daily-rotated audit log file path."""
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        return self._log_dir / f"audit-{date_str}.jsonl"

    def write(
        self,
        *,
        agent: str,
        contract_fingerprint: str,
        action: str,
        input_summary: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
        hitl_status: str | None = None,
        model: str | None = None,
        tokens_used: int | None = None,
        cost_usd: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append one audit entry to the daily JSONL log.

        All inputs/outputs are sanitized: long strings truncated,
        likely-PII fields hashed. Full contract text is NEVER stored.
        """
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "agent": agent,
            "contract_fingerprint": contract_fingerprint,
            "action": action,
            "input_summary": _sanitize_for_log(input_summary),
            "output_summary": _sanitize_for_log(output_summary),
            "hitl_status": hitl_status,
            "model": model,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "metadata": _sanitize_for_log(metadata),
            "system": {
                "pid": os.getpid(),
                "version": "0.1.0",
            },
        }

        log_file = self._current_file()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

        logger.debug(
            "audit_entry",
            agent=agent,
            action=action,
            contract=contract_fingerprint,
            file=str(log_file),
        )

    def read(
        self,
        contract_fingerprint: str | None = None,
        agent: str | None = None,
        date: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Read audit entries, optionally filtered.

        Used by the dashboard for audit log search.
        """
        entries: list[dict[str, Any]] = []

        # Determine which files to read
        if date:
            files = [self._log_dir / f"audit-{date}.jsonl"]
        else:
            files = sorted(self._log_dir.glob("audit-*.jsonl"))

        for log_file in files:
            if not log_file.exists():
                continue
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Apply filters
                    if contract_fingerprint and entry.get("contract_fingerprint") != contract_fingerprint:
                        continue
                    if agent and entry.get("agent") != agent:
                        continue

                    entries.append(entry)
                    if len(entries) >= limit:
                        return entries

        return entries

    def kill_switch(self) -> None:
        """Write a kill-switch audit entry and set the kill file."""
        self.write(
            agent="system",
            contract_fingerprint="ALL",
            action="KILL_SWITCH_ACTIVATED",
            output_summary={"status": "all_autonomous_activity_halted"},
        )
        kill_file = settings.output_dir / ".kill_switch"
        kill_file.touch()
        logger.critical("kill_switch_activated", file=str(kill_file))

    @staticmethod
    def is_killed() -> bool:
        """Check if the kill switch is active."""
        kill_file = settings.output_dir / ".kill_switch"
        return kill_file.exists()


# Module-level singleton
audit_log = AuditLogWriter()
