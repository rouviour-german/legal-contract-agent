"""
End-to-end tests for IntakeAgent.

Verifies that real contracts (PDF, DOCX) are parsed into
canonical Contract objects with grounding.
"""

import pytest
from pathlib import Path

from legal_agent.agents.intake import IntakeAgent
from legal_agent.models import ContractType, HITLStatus

FIXTURES_DIR = Path("tests/fixtures")


@pytest.mark.asyncio
async def test_intake_pdf_nda():
    """Test PDF parsing on a sample NDA."""
    file_path = FIXTURES_DIR / "sample-nda.pdf"
    raw_bytes = file_path.read_bytes()
    
    agent = IntakeAgent()
    state = {
        "raw_bytes": raw_bytes,
        "source_filename": "sample-nda.pdf",
    }
    
    result = await agent.run(state)
    
    assert "contract" in result
    contract = result["contract"]
    
    assert contract.file_type == "pdf"
    assert contract.contract_type == ContractType.NDA
    assert contract.type_confidence > 0.8
    assert len(contract.clauses) > 0
    
    # Grounding check
    clause = contract.clauses[0]
    assert clause.source_location is not None
    assert clause.source_location.page == 1
    assert len(clause.source_location.bounding_box) == 4


@pytest.mark.asyncio
async def test_intake_docx_msa():
    """Test DOCX parsing on a sample MSA."""
    file_path = FIXTURES_DIR / "sample-msa.docx"
    raw_bytes = file_path.read_bytes()
    
    agent = IntakeAgent()
    state = {
        "raw_bytes": raw_bytes,
        "source_filename": "sample-msa.docx",
    }
    
    result = await agent.run(state)
    
    assert "contract" in result
    contract = result["contract"]
    
    assert contract.file_type == "docx"
    assert contract.contract_type == ContractType.MSA
    assert "MASTER SERVICES AGREEMENT" in contract.full_text
    assert any("Scope" in c.heading for c in contract.clauses)


@pytest.mark.asyncio
async def test_intake_hitl_low_confidence():
    """Test low-confidence classification triggers HITL."""
    raw_bytes = b"This is a generic agreement with no keywords."
    
    agent = IntakeAgent()
    state = {
        "raw_bytes": raw_bytes,
        "source_filename": "generic.pdf",
    }
    
    result = await agent.run(state)
    
    assert "hitl_queue" in result
    queue = result["hitl_queue"]
    assert len(queue) == 1
    assert queue[0].item_type == "classification"
    assert "confidence low" in queue[0].reason
