"""
Command-line interface for the Legal Contract Agent.
"""

import typer
from pathlib import Path
from legal_agent.graph.supervisor import supervisor_graph, _default_state
from legal_agent.config import settings

app = typer.Typer()


def run_supervisor(raw_bytes: bytes, filename: str) -> dict:
    """Run the supervisor graph with the given contract data."""
    initial_state = _default_state()
    initial_state.raw_bytes = raw_bytes
    initial_state.source_filename = filename

    # Run the graph
    result = supervisor_graph.invoke(initial_state)
    return result


@app.command()
def process_contract(
    file_path: Path = typer.Argument(..., help="Path to the contract file to process"),
    output_dir: Path = typer.Option(None, help="Directory to save outputs"),
):
    """
    Process a contract file through the legal agent pipeline.
    """
    if not file_path.exists():
        typer.echo(f"Error: File {file_path} does not exist.")
        raise typer.Exit(1)

    # Read file
    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    # Run supervisor
    result = run_supervisor(raw_bytes, file_path.name)

    typer.echo("Contract processing complete.")
    typer.echo(f"Result: {result}")
    # TODO: Save outputs


@app.command()
def start_server(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
):
    """
    Start the FastAPI server.
    """
    typer.echo(f"Starting server on {host}:{port}...")
    from legal_agent.api.app import app
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    app()