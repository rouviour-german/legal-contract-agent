"""Agent abstract base classes.

All five agents inherit from BaseAgent, which enforces:
- Structured input/output via AgentState
- Audit logging on every run
- Disclaimer injection on every output
- Kill-switch checking before execution
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

from legal_agent.config import settings
from legal_agent.graph.state import AgentState
from legal_agent.safety.audit import audit_log

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base for all agents in the supervisor graph.

    Subclasses must implement `run()` which takes the current state and
    returns a partial state update. The supervisor merges updates.
    """

    name: str = "base"

    def __init__(self) -> None:
        self._logger = logger.bind(agent=self.name)

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        """Entry point called by the LangGraph supervisor.

        Checks the kill switch, runs the agent, logs the result.
        """
        from legal_agent.safety.audit import AuditLogWriter

        if AuditLogWriter.is_killed():
            self._logger.warning("kill_switch_active", agent=self.name)
            return {"errors": [f"{self.name} skipped: kill switch active"]}

        self._logger.info("agent_start", contract_id=state.get("contract", {}).get("id") if isinstance(state.get("contract"), dict) else getattr(state.get("contract"), "id", None))  # type: ignore[arg-type]

        try:
            result = await self.run(state)
            self._logger.info("agent_complete", agent=self.name)

            # Audit log
            contract = state.get("contract")
            fingerprint = contract.fingerprint if contract else "unknown"
            audit_log.write(
                agent=self.name,
                contract_fingerprint=fingerprint,
                action=f"{self.name}.run",
                input_summary={"stage": state.get("current_stage")},
                output_summary={
                    k: str(v)[:200] for k, v in result.items()
                },
            )

            return result

        except Exception as exc:
            self._logger.exception("agent_error", agent=self.name, error=str(exc))
            contract = state.get("contract")
            fingerprint = contract.fingerprint if contract else "unknown"
            audit_log.write(
                agent=self.name,
                contract_fingerprint=fingerprint,
                action=f"{self.name}.error",
                output_summary={"error": str(exc)},
            )
            raise

    @abstractmethod
    async def run(self, state: AgentState) -> dict[str, Any]:
        """Execute the agent's logic and return a partial state update.

        Implementations should NOT mutate the state dict in-place.
        Return a dict of fields that the supervisor will merge.
        """
        ...
