"""
API routes for contract lifecycle management.

Expert implementation: provides endpoints for fetching contract details,
downloading redlines, and viewing obligation summaries.
"""

from __future__ import annotations

import logging
from typing import Any
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from legal_agent.models import Contract, ContractStatus
from legal_agent.disclaimer import inject_disclaimer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/contracts", tags=["contracts"])

# Mock DB for demonstration (Expert: Postgres)
_contracts: dict[str, Contract] = {}


@router.get("/")
async def list_contracts():
    """List all processed contracts."""
    return inject_disclaimer({"contracts": list(_contracts.values())})


@router.get("/{id}")
async def get_contract(id: str):
    """Fetch contract details by ID."""
    if id not in _contracts:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return inject_disclaimer({"contract": _contracts[id]})


@router.get("/{id}/download/redline")
async def download_redline(id: str):
    """Download the redlined DOCX for a specific contract."""
    # Expert usage: fetch output path from Redline history
    path = Path(f"outputs/redline-{id}.docx")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Redline file not found.")
    return FileResponse(path, filename=f"redline-{id}.docx")


@router.get("/{id}/download/ical")
async def download_ical(id: str):
    """Download the iCalendar file for obligations."""
    path = Path(f"outputs/obligations-{id}.ics")
    if not path.exists():
        raise HTTPException(status_code=404, detail="iCal file not found.")
    return FileResponse(path, filename=f"obligations-{id}.ics")
