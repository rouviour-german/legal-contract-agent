"""
FastAPI application for the Legal Contract Agent.

Expert implementation: includes HITL routing, contract management,
and static dashboard hosting with structural disclaimers.
"""

from __future__ import annotations

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from legal_agent.api.middleware import disclaimer_middleware
from legal_agent.disclaimer import inject_disclaimer
from legal_agent.graph.supervisor import supervisor_graph
from legal_agent.graph.state import AgentState
from legal_agent.api.routes import hitl, contracts

app = FastAPI(title="Legal Contract Agent", version="0.1.0")

# 1. CORS for React Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Structural Disclaimer
app.middleware("http")(disclaimer_middleware)

# 3. Include Sub-routers
app.include_router(hitl.router)
app.include_router(contracts.router)


@app.post("/process-contract")
async def process_contract(file: UploadFile = File(...)):
    """
    Process a contract file through the legal agent pipeline.
    """
    raw_bytes = await file.read()

    # Run supervisor flow (Intake → Analysis → Playbook → Redline → Obligations)
    initial_state = AgentState(
        raw_bytes=raw_bytes,
        source_filename=file.filename,
        hitl_queue=[],
        next_stage="intake",
    )

    result = supervisor_graph.invoke(initial_state)
    
    # Store in mock DB for demonstration (Expert: DB persists this)
    contract = result.get("contract")
    if contract:
        contracts._contracts[contract.id] = contract
        
    return inject_disclaimer({"status": "processed", "result": result})


@app.get("/health")
async def health():
    """Health check endpoint."""
    return inject_disclaimer({"status": "healthy"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)