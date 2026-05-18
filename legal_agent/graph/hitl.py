"""Human-in-the-loop gate.

When any agent flags an action as `requires_approval=True`,
the item is written to the HITL queue and the workflow pauses
that branch until a human resolves it via the dashboard or CLI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from legal_agent.graph.state import AgentState
from legal_agent.models import HITLItem, HITLStatus

logger = structlog.get_logger(__name__)

# In-memory store for HITL resolutions (backed by Redis/Postgres in production)
_resolutions: dict[str, dict[str, Any]] = {}


def hitl_gate(state: AgentState) -> dict[str, Any]:
    """LangGraph node that checks for pending HITL items and blocks if needed.

    This node runs after every agent. If the agent produced HITL items,
    it checks whether they've been resolved. Unresolved items block the graph.
    """
    # Test mode: auto-approve all HITL items
    if state.get("test_mode", False):
        pending_items = state.get("hitl_queue", [])
        if pending_items:
            resolutions = state.get("hitl_resolutions", {})
            for item_data in pending_items:
                item = HITLItem.model_validate(item_data) if isinstance(item_data, dict) else item_data
                item_id = item.id if isinstance(item, HITLItem) else str(item_data.get("id", ""))
                if item_id not in resolutions:
                    resolutions[item_id] = {
                        "status": HITLStatus.APPROVED.value,
                        "resolved_by": "test_auto_approve",
                        "notes": "Auto-approved for testing",
                        "resolved_at": datetime.now(UTC).isoformat(),
                    }
            return {"hitl_resolutions": resolutions}
        return {}

    pending_items = state.get("hitl_queue", [])
    resolutions = state.get("hitl_resolutions", {})

    # Merge in-memory resolutions
    resolutions.update(_resolutions)

    still_pending: list[HITLItem] = []
    resolved_ids: list[str] = []

    for item_data in pending_items:
        item = HITLItem.model_validate(item_data) if isinstance(item_data, dict) else item_data
        item_id = item.id if isinstance(item, HITLItem) else str(item_data.get("id", ""))

        if item_id in resolutions:
            res = resolutions[item_id]
            item.status = HITLStatus(res.get("status", HITLStatus.APPROVED.value))
            item.resolved_at = datetime.now(UTC)
            item.resolved_by = res.get("resolved_by", "unknown")
            item.resolution_notes = res.get("notes")
            resolved_ids.append(item_id)
        else:
            still_pending.append(item)

    if still_pending:
        blocker_names = [
            str(i.item_data.get("term_name", "unknown")) for i in still_pending
        ]
        logger.info(
            "hitl_blocking",
            pending_count=len(still_pending),
            blockers=blocker_names,
        )
        return {
            "current_stage": "hitl_blocked",
        }

    if resolved_ids:
        logger.info("hitl_cleared", resolved=resolved_ids)

    return {}


def resolve_hitl(item_id: str, status: HITLStatus, resolved_by: str, notes: str | None = None) -> None:
    """Resolve a HITL item. Called by the dashboard/CLI API."""
    _resolutions[item_id] = {
        "status": status.value,
        "resolved_by": resolved_by,
        "notes": notes,
        "resolved_at": datetime.now(UTC).isoformat(),
    }
    logger.info("hitl_resolved", item_id=item_id, status=status.value, resolved_by=resolved_by)


def get_pending_hitl() -> list[dict[str, Any]]:
    """Return all pending HITL items for the dashboard."""
    return [
        item for item_list in _resolutions.values()
        for item in [item_list]  # type: ignore
        if item.get("status") == HITLStatus.PENDING.value  # type: ignore
    ]
