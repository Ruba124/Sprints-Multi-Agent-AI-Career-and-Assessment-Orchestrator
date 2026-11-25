import os
import re
import sys
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from state import OrchestratorState
from llm_provider import get_llm
from tools.db_queries import query_learner_db
from tools.rag_retriever import search_sprints_curriculum

llm = get_llm(temperature=0)
TIER1_PARTNERS = ("fawry", "instapay", "vodafone")


# --- 1. Intent & Identity Requirement Classifier ---
class AdvisorQueryIntent(BaseModel):
    requires_personal_record: bool = Field(
        description=(
            "True ONLY if the user is asking about their personal progress, scores, readiness, "
            "or applying/getting approved for a hiring partner. False for general questions about "
            "Sprints tracks, module prerequisites, or general curriculum recommendations."
        )
    )
    extracted_learner_id: str = Field(
        default="",
        description="Explicit learner ID like SPR-1001 if mentioned, otherwise empty string.",
    )
    extracted_name: str = Field(
        default="",
        description="Explicit student name if introduced (e.g., 'I am Ahmed Youssef'), otherwise empty string.",
    )


# --- 2. Self-Reflection Document Grader (US-02) ---
class DocumentGrade(BaseModel):
    is_relevant: bool = Field(
        description="True if the retrieved curriculum chunks contain relevant facts to answer the user's question."
    )
    reason: str = Field(description="Brief explanation of why the chunks are relevant or insufficient.")


intent_llm = llm.with_structured_output(AdvisorQueryIntent)
grader_llm = llm.with_structured_output(DocumentGrade)


class AdvisorState(OrchestratorState, total=False):
    search_query: str
    rag_context: str
    db_context: str
    rag_retries: int
    docs_relevant: bool
    needs_identity_prompt: bool
    hitl_approved: bool
    hitl_feedback: str


# --- Node 1: Resolve Learner Identity & Check if Personal Record Is Required ---
def resolve_identity_node(state: AdvisorState) -> dict:
    last_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break

    analysis: AdvisorQueryIntent = intent_llm.invoke([
        SystemMessage(
            content=(
                "Analyze the student's message to determine:\n"
                "1) Does answering this require looking up a personal student database record "
                "(e.g., checking their completed modules, scores, readiness status, or applying to a company)?\n"
                "2) Did they provide a Learner ID (SPR-XXXX) or their name?"
            )
        ),
        HumanMessage(content=last_msg),
    ])

    # Regex backup for SPR-XXXX
    regex_id = re.search(r"SPR-\d+", last_msg, re.IGNORECASE)
    learner_id = (
        (regex_id.group(0).upper() if regex_id else "")
        or analysis.extracted_learner_id.strip().upper()
        or state.get("learner_id", "")
    )
    student_name = analysis.extracted_name.strip()

    db_context = state.get("db_context", "")

    # Query SQLite ONLY when an explicit ID or Name is provided
    if learner_id:
        db_context = query_learner_db.invoke({
            "sql_query": f"SELECT * FROM learners WHERE learner_id = '{learner_id}'"
        })
    elif student_name:
        safe_name = student_name.replace("'", "''").lower()
        db_context = query_learner_db.invoke({
            "sql_query": f"SELECT * FROM learners WHERE LOWER(name) LIKE '%{safe_name}%'"
        })
        # Extract canonical learner_id if found in DB output
        found_id = re.search(r"SPR-\d+", db_context)
        if found_id:
            learner_id = found_id.group(0)

    # If personal record is required AND we still have neither ID nor DB record -> ask the user!
    if analysis.requires_personal_record and not db_context:
        print("[Advisor Identity Gate] Personal record required but no ID/Name provided -> Prompting user.")
        return {
            "needs_identity_prompt": True,
            "db_context": "",
        }

    return {
        "needs_identity_prompt": False,
        "learner_id": learner_id or None,
        "db_context": db_context,
        "search_query": last_msg,
        "rag_retries": 0,
    }


def route_after_identity(state: AdvisorState) -> Literal["ask_identity", "fetch_rag"]:
    return "ask_identity" if state.get("needs_identity_prompt") else "fetch_rag"


# --- Node 1b: Politely Ask for Learner ID or Full Name ---
def ask_identity_node(state: AdvisorState) -> dict:
    prompt_msg = (
        "To check your module progress, assessment scores, or placement eligibility, "
        "could you please share your **Sprints Learner ID** (for example, `SPR-1001`) or your **full name**?"
    )
    return {"messages": [AIMessage(content=prompt_msg)]}


# --- Node 2: Retrieve ChromaDB Curriculum (US-02) ---
def fetch_rag_node(state: AdvisorState) -> dict:
    last_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break

    active_query = state.get("search_query") or last_msg
    rag_context = search_sprints_curriculum.invoke({"query": active_query})

    return {
        "search_query": active_query,
        "rag_context": rag_context,
    }


# --- Node 3: Self-Reflection Document Grader (US-02) ---
def grade_documents_node(state: AdvisorState) -> dict:
    last_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break

    retries = state.get("rag_retries", 0)
    rag_context = state.get("rag_context", "")

    grade: DocumentGrade = grader_llm.invoke([
        SystemMessage(
            content=(
                "You are a strict retrieval quality grader for Sprints Bootcamp. "
                "Evaluate whether the retrieved curriculum excerpts contain concrete information "
                "needed to answer the user's question."
            )
        ),
        HumanMessage(
            content=f"User Question: {last_msg}\n\nRetrieved Curriculum Chunks:\n{rag_context}"
        ),
    ])

    print(f"[Advisor RAG Grader - Attempt {retries + 1}] Relevant={grade.is_relevant} | Reason: {grade.reason}")
    return {"docs_relevant": grade.is_relevant}


# --- Node 4: Query Rewriter for Self-Reflection Loop (US-02) ---
def rewrite_query_node(state: AdvisorState) -> dict:
    last_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break

    old_query = state.get("search_query", last_msg)
    retries = state.get("rag_retries", 0) + 1

    rewritten = llm.invoke([
        SystemMessage(
            content=(
                "Rewrite the user's question into a concise, keyword-rich search query for the "
                "Sprints curriculum and hiring partner vector database (tracks AI-101 to AI-104, BE-201, "
                "prerequisites, passing scores, Tier-1 partners Fawry/InstaPay/Vodafone, compensation). "
                "Return ONLY the rewritten query text."
            )
        ),
        HumanMessage(content=f"Original Question: {last_msg}\nPrevious Search Query: {old_query}"),
    ])

    new_query = rewritten.content.strip().strip('"')
    print(f"[Advisor Query Rewrite #{retries}] '{old_query}' -> '{new_query}'")
    return {
        "search_query": new_query,
        "rag_retries": retries,
    }


def decide_after_grading(state: AdvisorState) -> Literal["rewrite_query", "check_tier1_hitl"]:
    if state.get("docs_relevant", True) or state.get("rag_retries", 0) >= 2:
        return "check_tier1_hitl"
    return "rewrite_query"


# --- Node 5: Tier-1 Partner Human-in-the-Loop Escalation (US-04) ---
def check_tier1_hitl_node(state: AdvisorState) -> dict:
    last_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break

    matched_partners = [p.title() for p in TIER1_PARTNERS if p in last_msg.lower()]

    if matched_partners:
        partner_str = ", ".join(matched_partners)
        print(f"[Advisor HITL Trace] Tier-1 partner detected ({partner_str}) -> Pausing via interrupt() for coach review.")

        human_decision = interrupt({
            "event": "TIER_1_PLACEMENT_APPROVAL_REQUIRED",
            "learner_id": state.get("learner_id") or "Unverified Guest",
            "tier1_partner": partner_str,
            "student_query": last_msg,
            "db_summary": state.get("db_context") or "No learner database record attached.",
            "instruction": "Approve or reject Tier-1 placement recommendation.",
        })

        if isinstance(human_decision, dict):
            approved = bool(human_decision.get("approved", True))
            notes = str(human_decision.get("notes", ""))
        elif isinstance(human_decision, bool):
            approved = human_decision
            notes = ""
        else:
            approved = "approve" in str(human_decision).lower() or "yes" in str(human_decision).lower()
            notes = str(human_decision)

        print(f"[Advisor HITL Trace] Resumed with Approved={approved} | Notes='{notes}'")
        return {"hitl_approved": approved, "hitl_feedback": notes}

    return {"hitl_approved": True, "hitl_feedback": ""}


# --- Node 6: Final Response Synthesis ---
def generate_advisor_response_node(state: AdvisorState) -> dict:
    last_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break

    if not state.get("hitl_approved", True):
        coach_note = state.get("hitl_feedback", "Please complete pending modules before applying.")
        msg = (
            f"Your Tier-1 placement request was reviewed by a Sprints Career Coach and is currently "
            f"**on hold**. Coach feedback: {coach_note}"
        )
        return {"messages": [AIMessage(content=msg)]}

    if state.get("db_context"):
        combined_context = (
            f"=== LEARNER DB RECORD ===\n{state.get('db_context')}\n\n"
            f"=== CURRICULUM RAG ===\n{state.get('rag_context', '')}"
        )
    else:
        combined_context = f"=== CURRICULUM RAG ===\n{state.get('rag_context', '')}"

    coach_note = state.get("hitl_feedback", "")
    coach_clause = f"\nApproved Career Coach Note: {coach_note}" if coach_note else ""

    response = llm.invoke([
        SystemMessage(
            content=(
                "You are the Sprints Career & Curriculum Advisor. Answer the user's question clearly "
                "using ONLY the provided context. Never assume a student's name or ID if no Learner DB Record is present."
            )
        ),
        HumanMessage(content=f"Context:\n{combined_context}{coach_clause}\n\nUser Question: {last_msg}"),
    ])

    return {
        "retrieved_context": combined_context,
        "messages": [AIMessage(content=response.content)],
    }


# --- Compile Advisor Subgraph ---
advisor_builder = StateGraph(AdvisorState)
advisor_builder.add_node("resolve_identity", resolve_identity_node)
advisor_builder.add_node("ask_identity", ask_identity_node)
advisor_builder.add_node("fetch_rag", fetch_rag_node)
advisor_builder.add_node("grade_documents", grade_documents_node)
advisor_builder.add_node("rewrite_query", rewrite_query_node)
advisor_builder.add_node("check_tier1_hitl", check_tier1_hitl_node)
advisor_builder.add_node("generate_response", generate_advisor_response_node)

advisor_builder.set_entry_point("resolve_identity")
advisor_builder.add_conditional_edges(
    "resolve_identity",
    route_after_identity,
    {
        "ask_identity": "ask_identity",
        "fetch_rag": "fetch_rag",
    },
)
advisor_builder.add_edge("ask_identity", END)
advisor_builder.add_edge("fetch_rag", "grade_documents")
advisor_builder.add_conditional_edges(
    "grade_documents",
    decide_after_grading,
    {
        "rewrite_query": "rewrite_query",
        "check_tier1_hitl": "check_tier1_hitl",
    },
)
advisor_builder.add_edge("rewrite_query", "fetch_rag")
advisor_builder.add_edge("check_tier1_hitl", "generate_response")
advisor_builder.add_edge("generate_response", END)

advisor_subgraph = advisor_builder.compile()