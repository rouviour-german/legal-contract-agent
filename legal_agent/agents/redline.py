"""RedlineAgent generates a draft redline document and cover summary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from legal_agent.agents._base import BaseAgent
from legal_agent.config import settings
from legal_agent.graph.state import AgentState
from legal_agent.models import Deviation, Redline, RedlineClause, Severity
from legal_agent.redline.docx_writer import write_redline_docx
from legal_agent.disclaimer import disclaimer_footer


class RedlineAgent(BaseAgent):
    """Drafts a redline from deviations and prepares a document output."""

    name = "RedlineAgent"

    async def run(self, state: AgentState) -> dict[str, Any]:
        contract = state.get("contract")
        deviations = state.get("deviations", [])

        if contract is None:
            return {"errors": [f"{self.name}: missing contract"]}

        if not isinstance(deviations, list):
            deviations = []

        redline = Redline(contract_id=contract.id)
        requires_approval = False
        for deviation in deviations:
            if isinstance(deviation, dict):
                deviation = Deviation.model_validate(deviation)
            redline_clause = RedlineClause(
                clause_id=deviation.contract_id,
                original_text=str(deviation.extracted_value),
                revised_text=str(deviation.playbook_ideal),
                changes=[
                    {"type": "delete", "text": str(deviation.extracted_value)},
                    {"type": "insert", "text": str(deviation.playbook_ideal)},
                ],
                comment=deviation.explanation,
                source_location=deviation.source_location,
            )
            redline.clause_redlines.append(redline_clause)
            if deviation.severity == Severity.BLOCKER:
                requires_approval = True

        redline.requires_human_approval = requires_approval
        redline.cover_email_text = self._build_cover_email(deviations, contract)

        output_path = write_redline_docx(redline, contract, settings.output_dir)
        redline.output_path = str(output_path)

        return {
            "redline": redline,
        }

    def _build_cover_email(self, deviations: list[Deviation], contract: Any) -> str:
        lines = [
            f"Draft redline generated for contract {contract.source_filename}.",
            "Summary of deviations:",
        ]
        if not deviations:
            lines.append("No material deviations detected against the playbook.")
        else:
            for deviation in deviations:
                if isinstance(deviation, dict):
                    deviation = Deviation.model_validate(deviation)
                lines.append(
                    f"- {deviation.term_name}: {deviation.severity.value}. {deviation.explanation}"
                )
        lines.append("")
        lines.append("Review the attached redline and approve any blocker items before sending.")
        lines.append(disclaimer_footer())
        return "\n".join(lines)
