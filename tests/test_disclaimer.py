"""Tests for disclaimer injection and policy enforcement."""

from legal_agent.disclaimer import inject_disclaimer, DISCLAIMER_KEY


def test_inject_disclaimer_adds_machine_readable_payload():
    payload = {"status": "ok"}
    augmented = inject_disclaimer(payload)
    assert DISCLAIMER_KEY in augmented
    disclaimer_data = augmented[DISCLAIMER_KEY]
    assert "disclaimer" in disclaimer_data
    assert "short_disclaimer" in disclaimer_data
