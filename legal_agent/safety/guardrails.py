"""Safety guardrails: blocker gates and material-term enforcement."""

from __future__ import annotations

from legal_agent.models import Contract, Deviation, HITLItem, HITLStatus, Severity

# These clause types ALWAYS require human approval before any redline.
# No exceptions. This is the "no final-decision authority" rule in code.
BLOCKER_CLAUSE_TYPES = frozenset(
    {
        "indemnification",
        "limitation_of_liability",
        "liability_cap",
        "ip_assignment",
        "ip_ownership",
        "governing_law",
        "dispute_resolution",
        "arbitration",
        "non_compete",
        "non_solicit",
    }
)


def check_blocker_deviations(
    deviations: list[Deviation],
    contract: Contract,
) -> tuple[list[Deviation], list[HITLItem]]:
    """Separate deviations into autonomous vs HITL-required.

    Returns:
        (autonomous_deviations, hitl_items)

    A deviation requires human approval if:
    1. Its severity is BLOCKER, OR
    2. It touches any clause type in BLOCKER_CLAUSE_TYPES
    """
    autonomous: list[Deviation] = []
    hitl_items: list[HITLItem] = []

    for dev in deviations:
        is_blocker = (
            dev.severity == Severity.BLOCKER
            or _touches_material_clause(dev, contract)
        )

        if is_blocker:
            dev.requires_approval = True
            hitl_items.append(
                HITLItem(
                    contract_id=dev.contract_id,
                    agent_name="PlaybookAgent",
                    stage="playbook",
                    item_type="deviation",
                    item_data=dev.model_dump(mode="json"),
                    reason=(
                        f"Blocker deviation on '{dev.term_name}' "
                        f"(severity={dev.severity.value})"
                    ),
                    status=HITLStatus.PENDING,
                )
            )
        else:
            autonomous.append(dev)

    return autonomous, hitl_items


def _touches_material_clause(deviation: Deviation, contract: Contract) -> bool:
    """Check if a deviation touches a clause type requiring human approval."""
    if deviation.source_location and deviation.source_location.section_ref:
        # Check if the referenced clause is a blocker type
        clause = contract.find_clause_by_ref(deviation.source_location.section_ref)
        if clause and clause.clause_type in BLOCKER_CLAUSE_TYPES:
            return True

    # Also check by term name mapping
    term_to_clause = {
        "indemnification_cap": "indemnification",
        "liability_cap": "limitation_of_liability",
        "governing_law": "governing_law",
        "ip_assignment": "ip_assignment",
        "dispute_resolution": "dispute_resolution",
    }
    clause_type = term_to_clause.get(deviation.term_name)
    if clause_type and clause_type in BLOCKER_CLAUSE_TYPES:
        return True

    return False


def verify_clause_reference(contract: Contract, section_ref: str) -> bool:
    """Hallucination guardrail: verify a section reference exists before emitting it.

    Returns True if the reference is grounded in the actual parsed contract.
    Any time the system cites 'Section 4.2' or 'the Indemnification clause,'
    it MUST pass this check first.
    """
    return contract.has_section(section_ref)
