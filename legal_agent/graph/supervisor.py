"""
SupervisorAgent — orchestrates the five agents using LangGraph.

Expert implementation: handles state transitions, HITL gates, 
and sequential flow with the ability to pause for approval.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from langgraph.graph import END, StateGraph

from legal_agent.agents.analysis import AnalysisAgent
from legal_agent.agents.intake import IntakeAgent
from legal_agent.agents.obligations import ObligationsAgent
from legal_agent.agents.playbook import PlaybookAgent
from legal_agent.agents.redline import RedlineAgent
from legal_agent.graph.state import AgentState

logger = logging.getLogger(__name__)


def _route_next(state: AgentState) -> Literal["intake", "analysis", "playbook", "redline", "obligations", "__end__"]:
    """Determines the next agent based on the current state and HITL queue."""
    # Expert usage: if any 'blocker' items are in the hitl_queue, pause
    hitl_queue = state.get("hitl_queue", [])
    if hitl_queue and any(item.status == "pending" for item in hitl_queue):
        # We stop and wait for human input before proceeding to Redline/Obligations
        logger.info("⏸ PAUSE: HITL items pending approval.")
        return "__end__"  # In a real system, this would point to a 'hitl' node or wait
        
    # Standard flow
    # In a production system, we'd check 'last_agent' or current stage
    # For now, let's use a simplified sequence logic
    next_stage = state.get("next_stage", "intake")
    return next_stage


# Initialize Agents
intake_agent = IntakeAgent()
analysis_agent = AnalysisAgent()
playbook_agent = PlaybookAgent()
redline_agent = RedlineAgent()
obligations_agent = ObligationsAgent()


# Create Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("intake", intake_agent.run)
workflow.add_node("analysis", analysis_agent.run)
workflow.add_node("playbook", playbook_agent.run)
workflow.add_node("redline", redline_agent.run)
workflow.add_node("obligations", obligations_agent.run)

# Build Edges
workflow.set_entry_point("intake")

workflow.add_edge("intake", "analysis")
workflow.add_edge("analysis", "playbook")

# Conditional Routing for Blocker Items
def after_playbook(state: AgentState):
    """Wait for approval if blocker deviations or low-confidence found."""
    if state.get("hitl_queue"):
        return END
    return "redline"

workflow.add_conditional_edges("playbook", after_playbook)
workflow.add_edge("redline", "obligations")
workflow.add_edge("obligations", END)

# Compile
supervisor_graph = workflow.compile()
