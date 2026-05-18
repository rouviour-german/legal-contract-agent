"""
ObligationsAgent — identifies post-signing obligations for monitoring.

Expert implementation for Phase 6: proactive renewal detection,
notice periods, and calendar export for auditing.
"""

from __future__ import annotations

import logging
from typing import Any

from legal_agent.agents._base import BaseAgent
from legal_agent.config import settings
from legal_agent.graph.state import AgentState
from legal_agent.models import Obligation, ContractStatus
from legal_agent.obligations.extractor import ObligationExtractor
from legal_agent.obligations.calendar_writer import write_ical_file

logger = logging.getLogger(__name__)


class ObligationsAgent(BaseAgent):
    """Refined ObligationsAgent for Phase 6: extracts and exports to calendar."""

    name = "ObligationsAgent"

    async def run(self, state: AgentState) -> dict[str, Any]:
        contract = state.get("contract")
        if not contract:
            return {"errors": [f"{self.name}: no contract in state"]}

        # 1. Obligation Extraction (Expert: enhanced date detection)
        extractor = ObligationExtractor(contract)
        obligations = extractor.extract_obligations()

        # 2. Calendar Event Generation (Expert: iCal export)
        ical_path = settings.output_dir / f"obligations-{contract.id}.ics"
        if obligations:
            write_ical_file(obligations, ical_path)
            logger.info(f"Generated iCal file with {len(obligations)} events: {ical_path}")

        # 3. Mark Contract as Processed (Expert lifecycle)
        # Note: In a production system, this would only happen AFTER execution.
        contract.status = ContractStatus.UNDER_REVIEW

        return {
            "obligations": obligations,
            "ical_path": str(ical_path),
            "contract": contract,
        }
