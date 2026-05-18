"""PlaybookAgent compares extracted terms against the user's playbook."""

from __future__ import annotations

from typing import Any

from legal_agent.agents._base import BaseAgent
from legal_agent.graph.state import AgentState
from legal_agent.models import HITLItem, Playbook, PlaybookPosition
from legal_agent.playbook import load_playbook, match_playbook


class PlaybookAgent(BaseAgent):
    """Compares contract extraction results against a playbook."""

    name = "PlaybookAgent"

    async def run(self, state: AgentState) -> dict[str, Any]:
        contract = state.get("contract")
        term_sheet = state.get("term_sheet")

        if contract is None or term_sheet is None:
            return {"errors": [f"{self.name}: missing contract or term_sheet"]}

        playbook_path = state.get("playbook_path")
        playbook = load_playbook(playbook_path)

        deviations = match_playbook(playbook, contract, term_sheet)
        hitl_items: list[HITLItem] = []
        for deviation in deviations:
            if deviation.requires_approval:
                hitl_items.append(
                    HITLItem(
                        contract_id=contract.id,
                        agent_name=self.name,
                        stage="playbook",
                        item_type="deviation",
                        item_data=deviation.model_dump(mode="json"),
                        reason="Blocker deviation requires human approval.",
                    )
                )

        return {
            "playbook": playbook,
            "deviations": deviations,
            "hitl_queue": hitl_items,
        }
