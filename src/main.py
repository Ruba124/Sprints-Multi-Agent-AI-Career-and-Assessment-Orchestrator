from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import OrchestratorState
from agents.orchestrator import orchestrator_node, route_to_worker


# Temporary stubs for US-01 testing (will be replaced by US-02..US-07 implementations)
def advisor_stub(state: OrchestratorState) -> dict:
    """Temporary Advisor worker stub verifying routing and conversation history access."""
    turn_count = len(state["messages"])
    reply = f"[Advisor Agent] Received your career/curriculum request (History length: {turn_count} messages)."
    return {"messages": [AIMessage(content=reply)]}


def assessor_stub(state: OrchestratorState) -> dict:
    """Temporary Assessor worker stub verifying routing and conversation history access."""
    turn_count = len(state["messages"])
    reply = f"[Assessor Agent] Received your Python code for grading (History length: {turn_count} messages)."
    return {"messages": [AIMessage(content=reply)]}


def build_graph():
    """Compile the Sprints Multi-Agent StateGraph with MemorySaver checkpointing."""
    workflow = StateGraph(OrchestratorState)

    # 1. Add Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("advisor", advisor_stub)
    workflow.add_node("assessor", assessor_stub)

    # 2. Set Entry & Conditional Routing
    workflow.set_entry_point("orchestrator")
    workflow.add_conditional_edges(
        "orchestrator",
        route_to_worker,
        {
            "advisor": "advisor",
            "assessor": "assessor",
        }
    )

    # 3. Worker Exit Edges
    workflow.add_edge("advisor", END)
    workflow.add_edge("assessor", END)

    # 4. Compile with MemorySaver to isolate sessions by thread_id
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


if __name__ == "__main__":
    app = build_graph()

    # Thread 1: Student SPR-1001
    config_student_1 = {"configurable": {"thread_id": "SPR-1001"}}

    print("=== TEST 1: Career Question (Student SPR-1001, Turn 1) ===")
    res1 = app.invoke(
        {"messages": [HumanMessage(content="Hi, I'm Ahmed (SPR-1001). What modules do I need for Fawry?")]},
        config=config_student_1
    )
    print(res1["messages"][-1].content)

    print("\n=== TEST 2: Follow-up Code Submission (Student SPR-1001, Turn 2 - Tests Memory!) ===")
    res2 = app.invoke(
        {"messages": [HumanMessage(content="Can you grade this snippet? def add(a, b): return a + b")]},
        config=config_student_1
    )
    print(res2["messages"][-1].content)

    print("\n=== TEST 3: Separate Student Thread (Student SPR-1002 - Tests Isolation!) ===")
    config_student_2 = {"configurable": {"thread_id": "SPR-1002"}}
    res3 = app.invoke(
        {"messages": [HumanMessage(content="What is my target salary in EGP?")]},
        config=config_student_2
    )
    print(res3["messages"][-1].content)