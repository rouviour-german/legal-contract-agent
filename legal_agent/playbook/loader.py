from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from legal_agent.models import Playbook, PlaybookPosition, Severity


def default_playbook() -> Playbook:
    """Return a default fallback playbook for pipeline runs."""
    positions = {
        "*": {
            "term_length": PlaybookPosition(
                term_name="term_length",
                ideal="12 months",
                acceptable="12-24 months",
                walk_away=">24 months",
                severity_map={"default": Severity.MEDIUM.value},
                fallback_language="The term shall be 12 months with automatic renewal only upon mutual agreement.",
                notes="Standard contract term length for routine agreements.",
            ),
            "governing_law": PlaybookPosition(
                term_name="governing_law",
                ideal="Delaware",
                acceptable="New York",
                walk_away="Other",
                severity_map={"default": Severity.HIGH.value},
                fallback_language="The agreement shall be governed by Delaware law.",
                notes="Preferred venue for commercial contracts.",
            ),
        }
    }

    expected_clauses = {
        "NDA": ["confidentiality", "term", "termination"],
        "MSA": ["scope", "payment", "termination", "liability", "intellectual_property"],
        "SAAS": ["service_level", "data_security", "support", "termination", "liability"],
    }

    return Playbook(
        name="Default Contract Playbook",
        positions=positions,
        expected_clauses=expected_clauses,
    )


def load_playbook(path: Path | None = None) -> Playbook:
    """Load a playbook from YAML, or return the default playbook."""
    if path is None or not path.exists():
        return default_playbook()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    positions: dict[str, dict[str, PlaybookPosition]] = {}
    expected_clauses: dict[str, list[str]] = {}

    for contract_type, type_config in data.get("positions", {}).items():
        positions[contract_type] = {}
        for term_name, term_data in type_config.items():
            positions[contract_type][term_name] = PlaybookPosition(
                term_name=term_name,
                ideal=term_data.get("ideal"),
                acceptable=term_data.get("acceptable"),
                walk_away=term_data.get("walk_away"),
                severity_map=term_data.get("severity_map", {}),
                fallback_language=term_data.get("fallback_language"),
                notes=term_data.get("notes"),
                condition=term_data.get("condition"),
            )

    expected_clauses = data.get("expected_clauses", {}) or {}

    return Playbook(
        name=data.get("name", "Custom Contract Playbook"),
        version=data.get("version", "1.0.0"),
        positions=positions,
        expected_clauses=expected_clauses,
    )
