# import re
# import os
# import sys
# from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver

# # Ensure project root and src/ are on sys.path whether run via `python src/main.py` or `python -m src.main`
# ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# SRC_DIR = os.path.abspath(os.path.dirname(__file__))
# for path in (ROOT_DIR, SRC_DIR):
#     if path not in sys.path:
#         sys.path.insert(0, path)

# from state import OrchestratorState
# from llm_provider import get_llm
# from agents.orchestrator import orchestrator_node, route_to_worker
# from agents.assessor_agent import assessor_subgraph
# from tools.db_queries import query_learner_db
# from tools.rag_retriever import search_sprints_curriculum

# llm = get_llm(temperature=0)


# def advisor_rag_db_node(state: OrchestratorState) -> dict:
#     """
#     End-to-end integration node testing US-02 (ChromaDB RAG)
#     and US-03 (SQLite Learner DB) together inside main.py before adding US-04 HITL.
#     """
#     last_msg = ""
#     for msg in reversed(state["messages"]):
#         if isinstance(msg, HumanMessage):
#             last_msg = msg.content
#             break

#     # 1. Extract learner_id if mentioned (e.g., SPR-1001) and query SQLite DB (US-03)
#    # 1. Extract learner_id if mentioned (e.g., SPR-1001) and query SQLite DB (US-03)
#     id_match = re.search(r"SPR-\d+", last_msg, re.IGNORECASE)
#     learner_id = id_match.group(0).upper() if id_match else "SPR-1001"
#     db_result = query_learner_db.invoke({
#         "sql_query": f"SELECT * FROM learners WHERE learner_id = '{learner_id}'"
#     })

#     # 2. Query ChromaDB curriculum vector store (US-02)
#     rag_result = search_sprints_curriculum.invoke({"query": last_msg})

#     # 3. Synthesize grounded response
#     combined_context = (
#         f"=== LEARNER DB RECORD ({learner_id}) ===\n{db_result}\n\n"
#         f"=== CURRICULUM RAG ===\n{rag_result}"
#     )
#     response = llm.invoke([
#         SystemMessage(
#             content=(
#                 "You are the Sprints Career & Curriculum Advisor. Answer the student's question "
#                 "using ONLY the provided Learner DB Record and Curriculum RAG context."
#             )
#         ),
#         HumanMessage(content=f"Context:\n{combined_context}\n\nStudent Question: {last_msg}"),
#     ])

#     return {
#         "learner_id": learner_id,
#         "retrieved_context": combined_context,
#         "messages": [AIMessage(content=response.content)],
#     }


# # Build Master Graph
# workflow = StateGraph(OrchestratorState)
# workflow.add_node("orchestrator", orchestrator_node)
# workflow.add_node("assessor_agent", assessor_subgraph)
# workflow.add_node("advisor_agent", advisor_rag_db_node)

# workflow.set_entry_point("orchestrator")
# workflow.add_conditional_edges(
#     "orchestrator",
#     route_to_worker,
#     {
#         "assessor": "assessor_agent",
#         "advisor": "advisor_agent",
#     },
# )
# workflow.add_edge("assessor_agent", END)
# workflow.add_edge("advisor_agent", END)

# # Compile with MemorySaver for multi-turn session isolation (US-01)
# memory = MemorySaver()
# app = workflow.compile(checkpointer=memory)


# if __name__ == "__main__":
#     print("==========================================================")
#     print("  END-TO-END INTEGRATION TEST (ALL 3 TOOLS IN MAIN.PY)")
#     print("==========================================================")

#     # --- TEST 1: Advisor Route (Tests Tool #1 SQLite DB + Tool #2 ChromaDB RAG) ---
#     config_student_1 = {"configurable": {"thread_id": "session_spr_1001"}}
#     print("\n--- [1] Testing Advisor Route (SQLite DB + ChromaDB RAG) ---")
#     res_1 = app.invoke(
#         {
#             "messages": [
#                 HumanMessage(
#                     content="Hi, I'm SPR-1001. What modules and score do I need to apply to Fawry?"
#                 )
#             ]
#         },
#         config=config_student_1,
#     )
#     print(f"Routed Agent: {res_1.get('next_agent')}")
#     print(f"Final Answer:\n{res_1['messages'][-1].content}\n")

#     # --- TEST 2: Assessor Route (Tests Tool #3 Python REPL + Pydantic Grader + Judge Loop) ---
#     config_student_2 = {"configurable": {"thread_id": "session_spr_1002"}}
#     print("--- [2] Testing Assessor Route (Python REPL + Evaluator-Optimizer) ---")
#     res_2 = app.invoke(
#         {
#             "messages": [
#                 HumanMessage(
#                     content="Grade my Python factorial code:\n```python\ndef fact(n):\n    return 1 if n <= 1 else n * fact(n-1)\nprint(fact(5))\n```"
#                 )
#             ]
#         },
#         config=config_student_2,
#     )
#     print(f"Routed Agent: {res_2.get('next_agent')}")
#     print(f"Final Answer:\n{res_2['messages'][-1].content}\n")

#     # --- TEST 3: MemorySaver Isolation Check ---
#     print("--- [3] Verifying MemorySaver Session Isolation ---")
#     state_1 = app.get_state(config_student_1).values
#     state_2 = app.get_state(config_student_2).values
#     print(f"Session 1 Agent: {state_1.get('next_agent')} | Learner ID: {state_1.get('learner_id')}")
#     print(
#         f"Session 2 Agent: {state_2.get('next_agent')} | "
#         f"Score: {state_2.get('grading_result').score if state_2.get('grading_result') else 'N/A'}"
#     )

import os
import sys
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.abspath(os.path.dirname(__file__))
for path in (ROOT_DIR, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from state import OrchestratorState
from agents.orchestrator import orchestrator_node, route_to_worker
from agents.assessor_agent import assessor_subgraph
from agents.advisor_agent import advisor_subgraph

# Build Master Graph
workflow = StateGraph(OrchestratorState)
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("assessor_agent", assessor_subgraph)
workflow.add_node("advisor_agent", advisor_subgraph)

workflow.set_entry_point("orchestrator")
workflow.add_conditional_edges(
    "orchestrator",
    route_to_worker,
    {
        "assessor": "assessor_agent",
        "advisor": "advisor_agent",
    },
)
workflow.add_edge("assessor_agent", END)
workflow.add_edge("advisor_agent", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)


if __name__ == "__main__":
    print("==========================================================")
    print("  FULL CAPSTONE VERIFICATION (ALL 8 USER STORIES)")
    print("==========================================================")

    # --- TEST 1: Standard Curriculum Query + Self-Reflection RAG (US-01, US-02, US-03) ---
    cfg_1 = {"configurable": {"thread_id": "session_curriculum_1"}}
    print("\n--- [1] Advisor Standard / Self-Reflection RAG Test ---")
    res_1 = app.invoke(
        {"messages": [HumanMessage(content="I am SPR-1001. What prerequisites do I need before taking LangGraph?")]},
        config=cfg_1,
    )
    print(f"Final Answer:\n{res_1['messages'][-1].content}\n")

    # --- TEST 2: Tier-1 Partner HITL Pause & Resume (US-04) ---
    cfg_2 = {"configurable": {"thread_id": "session_fawry_hitl"}}
    print("--- [2] Tier-1 Partner HITL Escalation Test (Fawry) ---")
    res_2 = app.invoke(
        {"messages": [HumanMessage(content="Hi, I'm SPR-1001. Can you approve my placement application to Fawry?")]},
        config=cfg_2,
    )

    # Check if graph paused on interrupt()
    snapshot = app.get_state(cfg_2)
    if snapshot.next:
        print(f"Graph PAUSED at node: {snapshot.next}")
        print(f"Interrupt Payload: {snapshot.tasks[0].interrupts[0].value}")

        # Simulate Human Career Coach approving the placement
        print("\n[Human Coach] Approving Tier-1 placement via Command(resume=...)...")
        res_2_final = app.invoke(
            Command(resume={"approved": True, "notes": "Verified SPR-1001 meets all Fawry criteria. Cleared for referral!"}),
            config=cfg_2,
        )
        print(f"Final Resumed Answer:\n{res_2_final['messages'][-1].content}\n")

    # --- TEST 3: Assessor Code Grading Loop (US-05, US-06, US-07) ---
    cfg_3 = {"configurable": {"thread_id": "session_assessor_1"}}
    print("--- [3] Assessor Evaluator-Optimizer Test ---")
    res_3 = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Grade my Python factorial code:\n```python\ndef fact(n):\n    return 1 if n <= 1 else n * fact(n-1)\nprint(fact(5))\n```"
                )
            ]
        },
        config=cfg_3,
    )
    print(f"Final Answer:\n{res_3['messages'][-1].content}\n")