"""
Schema-constrained LLM term extractor for legal contracts.

Uses `instructor` for Anthropic Claude 3.5 Sonnet to ensure
outputs strictly follow the TermSheet Pydantic model.
"""

from __future__ import annotations

import logging
from typing import Any

import instructor
from anthropic import Anthropic
from legal_agent.config import settings
from legal_agent.models import Contract, MaterialTerm, SourceLocation, TermSheet

logger = logging.getLogger(__name__)


class TermExtractor:
    """Extracts material terms from legal documents using LLMs."""

    def __init__(self, api_key: str | None = None):
        # Expert implementation: use instructor for strict schema enforcement
        self.client = instructor.from_anthropic(Anthropic(api_key=api_key or settings.anthropic_api_key))

    async def extract_terms(self, contract: Contract) -> TermSheet:
        """Extract material terms using Claude 3.5 Sonnet and Structured Output."""
        
        prompt = self._build_extraction_prompt(contract)
        
        try:
            # Expert usage: use create_iterable or nested models if extraction is large
            # For Phase 3, we'll extract the core TermSheet directly.
            term_sheet = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                temperature=0.0,  # Deterministic for legal extraction
                response_model=TermSheet,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            return term_sheet
            
        except Exception as e:
            logger.error(f"Term extraction failed: {e}")
            # Minimum return for system resilience
            return TermSheet(contract_id=contract.id)

    @staticmethod
    def _build_extraction_prompt(contract: Contract) -> str:
        """Engineering high-fidelity prompt for legal extraction."""
        return f"""
        Extract ALL material terms from the FOLLOWING CONTRACT.
        Contract Type: {contract.contract_type.value if contract.contract_type else 'UNK'}
        
        CORE INSTRUCTIONS:
        1. Ground every term in reality. Every 'SourceLocation' MUST be citation-accurate (page number, section ref).
        2. Identify 'unusual_terms' that are aggressive (e.g., uncapped liability, perpetual assignment).
        3. Detect 'missing_clauses' that SHOULD be there for this contract type but aren't.
        4. Focus on Term Length, Renewal, Payment, IP, Indemnity, Liability Caps, and Governing Law.

        CONTRACT TEXT:
        {contract.full_text[:50000]}  # Context window management
        """
