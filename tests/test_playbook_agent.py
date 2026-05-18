"""Tests for playbook matching and deviation generation."""

from legal_agent.models import Contract, ContractType, MaterialTerm, SourceLocation, TermSheet
from legal_agent.playbook import default_playbook, match_playbook


def test_default_playbook_matches_term_sheet():
    contract = Contract(
        source_filename="test.pdf",
        source_hash="abc123",
        file_type="pdf",
        contract_type=ContractType.NDA,
        type_confidence=0.95,
        full_text="Test contract text.",
        status="draft",
    )
    term_sheet = TermSheet(contract_id=contract.id)
    term_sheet.terms["governing_law"] = MaterialTerm(
        name="governing_law",
        value="New York",
        source_location=SourceLocation(page=1, section_ref="Section 12"),
        confidence=0.95,
    )
    playbook = default_playbook()
    deviations = match_playbook(playbook, contract, term_sheet)

    assert len(deviations) == 1
    assert deviations[0].term_name == "governing_law"
    assert deviations[0].playbook_ideal == "Delaware"
    assert deviations[0].severity.name in {"MEDIUM", "HIGH", "BLOCKER", "LOW"}
