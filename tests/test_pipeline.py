"""End-to-end pipeline tests for the legal contract agent."""

from pathlib import Path
from legal_agent.graph.supervisor import supervisor_graph, _default_state


def test_supervisor_pipeline_runs_end_to_end(tmp_path: Path):
    """The supervisor graph should complete all stages for a dummy contract."""
    sample_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    initial_state = _default_state()
    initial_state["raw_bytes"] = sample_bytes
    initial_state["source_filename"] = "sample.pdf"
    initial_state["current_stage"] = "intake"
    initial_state["test_mode"] = True  # Auto-approve HITL items for testing

    result = supervisor_graph.invoke(initial_state)

    assert result.get("contract") is not None
    assert result.get("term_sheet") is not None
    assert result.get("deviations") is not None
    assert result.get("redline") is not None
    assert result.get("obligations") is not None
    assert result["current_stage"] == "done" or result.get("current_stage") is None
    redline = result["redline"]
    assert redline.output_path is not None
    assert Path(redline.output_path).exists()
