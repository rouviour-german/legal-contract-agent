"""Event-to-agent routing logic for the supervisor graph.

Determines which agents to invoke based on the event type
(e.g., new contract upload vs. counterparty redline review).
"""

from __future__ import annotations

from legal_agent.config import ContractStage


class Router:
    """Determines the execution path for a given contract event."""

    def __init__(self) -> None:
        pass

    def route_new_contract(self) -> list[str]:
        """Full pipeline for a new contract upload."""
        return ["intake", "analysis", "playbook", "redline", "obligations"]

    def route_counterparty_redline(self) -> list[str]:
        """Counterparty sent back redlines — skip intake, go straight to analysis on the diff."""
        return ["analysis", "playbook", "redline"]

    def route_obligations_only(self) -> list[str]:
        """Contract was marked executed externally — just extract obligations."""
        return ["obligations"]

    def should_skip_stage(self, stage: ContractStage, skip_stages: list[str]) -> bool:
        """Check if a stage should be skipped."""
        return stage.value in skip_stages
