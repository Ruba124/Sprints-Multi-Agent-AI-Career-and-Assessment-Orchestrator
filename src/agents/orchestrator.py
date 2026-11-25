import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
import sys
# Add the project root directory to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.state import OrchestratorState
from src.llm_provider import get_llm

load_dotenv()

class RouteDecision(BaseModel):
    """Structured routing schema for the Sprints Orchestrator."""
    next_agent: Literal["advisor", "assessor"] = Field(
        description=(
            "Route to 'assessor' if the user submits Python code for grading, "
            "debugging, or technical evaluation. Route to 'advisor' if the user asks "
            "about Sprints curriculum topics, bootcamp progress, target EGP salary, "
            "or career/employer placement (e.g., Fawry, Swvl)."
        )
    )
    reasoning: str = Field(
        description="Brief explanation of why this worker agent was selected."
    )


llm = get_llm(temperature=0)  # Deterministic output for routing decisions

router_llm = llm.with_structured_output(RouteDecision)

ROUTER_SYSTEM_PROMPT = """You are the central Sprints Multi-Agent Orchestrator.
Analyze the student's latest message alongside the conversation history and route them to the correct specialist:
1. 'assessor': The student pasted Python code, asked for code grading/evaluation, or wants feedback on a coding assignment.
2. 'advisor': The student is asking about Sprints bootcamp curriculum, learning modules, their learner profile/progress, target EGP salary, or job placement advice.

Always consider multi-turn context (e.g., if the student says 'now check my second attempt' after a coding question, route to 'assessor')."""


def orchestrator_node(state: OrchestratorState) -> dict:
    """
    Central Orchestrator node that classifies student intent and sets `next_agent`
    to dynamically route execution to either the Advisor or Assessor worker.
    """
    messages = [SystemMessage(content=ROUTER_SYSTEM_PROMPT)] + list(state["messages"])
    decision: RouteDecision = router_llm.invoke(messages)

    print(f"[Orchestrator Trace] Routed to -> '{decision.next_agent}' | Reason: {decision.reasoning}")
    return {"next_agent": decision.next_agent}


def route_to_worker(state: OrchestratorState) -> str:
    """Conditional edge function reading the Orchestrator's routing decision."""
    return state["next_agent"]