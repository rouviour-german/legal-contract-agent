"""
Hybrid rule + LLM classifier for contract types (NDA, MSA, DPA, SaaS, etc).

Expert implementation uses weighted keyword-based heuristics plus
confidence scoring for routing to HITL.
"""

from __future__ import annotations

import re
from typing import Tuple

from legal_agent.models import ContractType


class TypeClassifier:
    """Classifies contract types using internal heuristics."""

    def __init__(self, text: str):
        self.text = text.lower()

    def classify(self) -> Tuple[ContractType, float]:
        """Classify contract type with confidence scoring."""
        # Weighted rule-based classifier (Phase 2 expert: use regex with weights)
        rules = {
            ContractType.NDA: {
                r"\bnon-disclosure agreement\b": 0.9,
                r"\bconfidentiality agreement\b": 0.8,
                r"\bnda\b": 0.3,
            },
            ContractType.MSA: {
                r"\bmaster services agreement\b": 0.9,
                r"\bservices agreement\b": 0.5,
                r"\bmsa\b": 0.3,
            },
            ContractType.DPA: {
                r"\bdata processing addendum\b": 0.9,
                r"\bdata protection agreement\b": 0.8,
                r"\bdpa\b": 0.3,
            },
            ContractType.SAAS: {
                r"\bsoftware as a service\b": 0.9,
                r"\bsubscription agreement\b": 0.7,
                r"\bsaas\b": 0.3,
            },
        }

        best_type = ContractType.OTHER
        max_score = 0.0

        for ctype, pattern_map in rules.items():
            score = 0.0
            for pattern, weight in pattern_map.items():
                if re.search(pattern, self.text):
                    score = max(score, weight)
            
            if score > max_score:
                max_score = score
                best_type = ctype

        return best_type, max_score
