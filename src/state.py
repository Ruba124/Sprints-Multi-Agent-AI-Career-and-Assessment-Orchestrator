from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class OrchestratorState(TypedDict):
    """
    Global shared state passed between the Orchestrator, Advisor Agent,
    Assessor Agent, LLM Judge, and Human-in-the-Loop nodes.
    """
    # Standardized conversation & tool-call history (appends automatically)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Routing & Student Context
    next_agent: str                     # 'advisor' or 'assessor'
    student_id: Optional[str]           # e.g., 'SPR-1001'

    # Assessor Agent & Evaluator-Optimizer Loop State
    code_submission: Optional[str]      # Student's Python snippet to grade
    grade_result: Optional[dict]        # Structured Pydantic output: {score, feedback_points, pass_status}
    judge_feedback: Optional[str]       # Critique from the LLM-as-a-Judge node
    iteration_count: int                # Tracks refinement loops (strictly capped at 3)

    # Advisor Agent & Human-in-the-Loop (HITL) State
    retrieved_context: Optional[str]    # Curriculum chunks fetched from ChromaDB
    retrieval_attempts: int             # Tracks Agentic RAG query-rewrite loops
    recommended_employer: Optional[str] # e.g., 'Fawry', 'Swvl'
    placement_approved: Optional[bool]  # Set after human approval via interrupt()