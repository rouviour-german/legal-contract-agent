from __future__ import annotations

from typing import Any

from legal_agent.models import Contract, Deviation, Playbook, Severity, SourceLocation, TermSheet


def _classify_severity(position: Any, extracted_value: Any) -> Severity:
    if not position:
        return Severity.LOW
    if isinstance(position.severity_map, dict):
        candidate = position.severity_map.get(str(extracted_value))
        if candidate:
            return Severity(candidate)
        if "default" in position.severity_map:
            return Severity(position.severity_map["default"])
    return Severity.MEDIUM


def _explanation_for(position: Any, extracted_value: Any) -> str:
    return (
        f"The contract contains '{extracted_value}' for '{position.term_name}', "
        f"which differs from the playbook ideal '{position.ideal}'."
    )


def match_playbook(
    playbook: Playbook,
    contract: Contract,
    term_sheet: TermSheet,
) -> list[Deviation]:
    deviations: list[Deviation] = []

    contract_type = contract.contract_type.value if contract.contract_type else "*"

    for term_name, material in term_sheet.terms.items():
        position = playbook.get_position(contract_type, term_name)
        if position is None:
            continue

        if material.value != position.ideal:
            severity = _classify_severity(position, material.value)
            requires_approval = severity == Severity.BLOCKER
            deviations.append(
                Deviation(
                    contract_id=contract.id,
                    term_name=term_name,
                    extracted_value=material.value,
                    playbook_ideal=position.ideal,
                    playbook_acceptable=position.acceptable,
                    severity=severity,
                    explanation=_explanation_for(position, material.value),
                    fallback_position=position.fallback_language,
                    source_location=material.source_location,
                    requires_approval=requires_approval,
                )
            )

    for missing in term_sheet.missing_clauses:
        deviations.append(
            Deviation(
                contract_id=contract.id,
                term_name=f"missing_clause_{missing}",
                extracted_value="missing",
                playbook_ideal=missing,
                playbook_acceptable=None,
                severity=Severity.MEDIUM,
                explanation=f"Expected clause '{missing}' is missing from the contract.",
                fallback_position=f"Add a '{missing}' clause consistent with the playbook.",
                requires_approval=False,
            )
        )

    return deviations
