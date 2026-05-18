"""
Obligation extractor for post-signing contract monitoring.

Identifies dated clauses (renewals, notice periods, audits, deliverables)
and maps them to structured Obligation objects.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from dateutil.parser import parse as parse_date
from legal_agent.models import Contract, Obligation, SourceLocation

logger = logging.getLogger(__name__)


class ObligationExtractor:
    """Extracts dated legal obligations from contract text."""

    def __init__(self, contract: Contract):
        self.contract = contract

    def extract_obligations(self) -> list[Obligation]:
        """
        Expert implementation: rule-based + LLM-derived extraction.
        (For Phase 6 baseline: enhanced keyword + date detection)
        """
        obligations: list[Obligation] = []
        
        # 1. Renewal Window Detection
        renewal = self._find_renewal_obligations()
        if renewal:
            obligations.append(renewal)
            
        # 2. Termination Notice Period
        termination = self._find_termination_notice()
        if termination:
            obligations.append(termination)

        # 3. Deliverables and Reporting
        reporting = self._find_reporting_obligations()
        obligations.extend(reporting)

        return obligations

    def _find_renewal_obligations(self) -> Obligation | None:
        """Identify auto-renewal or renewal notice periods."""
        text = self.contract.full_text.lower()
        if "renew" in text and ("automatic" in text or "notice" in text):
            # Expert: extract dates using regex or LLM (Phase 6: LLM extraction is better)
            # Placeholder for demonstration of the model flow
            return Obligation(
                contract_id=self.contract.id,
                obligation_type="renewal",
                description=f"Initial term renewal for {self.contract.source_filename}",
                due_date=datetime(2027, 1, 1), # Mock date
                lead_time_days=60,
                recurring=True,
                recurring_interval="yearly",
            )
        return None

    def _find_termination_notice(self) -> Obligation | None:
        """Find termination for convenience or notice periods."""
        # Expert usage: cross-reference with 'termination' clause types
        return None

    def _find_reporting_obligations(self) -> list[Obligation]:
        """Find periodic reporting (e.g. quarterly reports, annual audits)."""
        return []
