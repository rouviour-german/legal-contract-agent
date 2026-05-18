"""Shared typed state for the LangGraph StateGraph.

Every node reads and returns this state. No in-place mutation —
each node returns a dict of fields to merge into the shared state.
"""

from __future__ import annotations

from typing import Any, NotRequired

from typing_extensions import TypedDict

from legal_agent.models import (
    Contract,
    Deviation,
    HITLItem,
    Obligation,
    Playbook,
    Redline,
    TermSheet,
)


class AgentState(TypedDict, total=False):
    """Shared state flowing through the supervisor graph.

    Fields are typed NotRequired so nodes can return only what they touch.
    """

    # Input
    raw_bytes: bytes
    source_filename: str

    # Core objects
    contract: Contract
    term_sheet: TermSheet
    playbook: Playbook
    deviations: list[Deviation]
    redline: Redline | None
    obligations: list[Obligation]

    # HITL
    hitl_queue: list[HITLItem]
    hitl_resolutions: dict[str, dict[str, Any]]  # HITLItem.id → resolution

    # Audit
    audit_log: list[dict[str, Any]]

    # Execution control
    current_stage: str
    skip_stages: list[str]
    kill_switch: bool
    errors: list[str]
