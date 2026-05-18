"""
API routes for Human-in-the-loop (HITL) approval queue.

Expert implementation: provides endpoints for fetching pending approvals,
resolving blocker deviations, and redline confirmations.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from legal_agent.models import HITLItem, HITLStatus
from legal_agent.disclaimer import inject_disclaimer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hitl", tags=["hitl"])

# Mock In-memory Queue for demonstration (Expert: Postgres)
_hitl_queue: dict[str, HITLItem] = {}


@router.get("/queue")
async def get_queue(status: HITLStatus | None = None):
    """Fetch the current HITL queue, filtered by status."""
    items = list(_hitl_queue.values())
    if status:
        items = [i for i in items if i.status == status]
    return inject_disclaimer({"items": items})


@router.post("/{item_id}/resolve")
async def resolve_item(item_id: str, resolution: dict[str, Any]):
    """Resolve a pending HITL item (approve/reject/escalate)."""
    if item_id not in _hitl_queue:
        raise HTTPException(status_code=404, detail="HITL item not found.")
        
    item = _hitl_queue[item_id]
    item.status = HITLStatus(resolution.get("status", HITLStatus.APPROVED))
    item.resolution_notes = resolution.get("notes")
    
    # Expert usage: log to safety audit trail
    logger.info(f"PHASE/HITL: {item_id} resolved as {item.status}")
    
    return inject_disclaimer({"status": "resolved", "item": item})
