"""Tests for the CLI."""

import pytest
from typer.testing import CliRunner
from legal_agent.cli import app

runner = CliRunner()


def test_process_contract_missing_file():
    """Test processing a non-existent file."""
    result = runner.invoke(app, ["process-contract", "nonexistent.pdf"])
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_start_server():
    """Test start server command help."""
    result = runner.invoke(app, ["start-server", "--help"])
    assert result.exit_code == 0
    assert "Start the FastAPI server" in result.output