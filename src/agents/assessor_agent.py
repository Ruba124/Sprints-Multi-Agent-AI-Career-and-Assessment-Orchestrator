import os
import sys
import json
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pathlib import Path

# Ensure project root is on sys.path whether run directly or imported from main.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.llm_provider import get_llm
from src.state import OrchestratorState
from src.tools.code_repl import execute_student_code
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)

load_dotenv()

MAX_ITERATIONS = 3  # Acceptance Criterion: strictly halt after 3 refinement iterations


# ==============================================================================
# 1. Pydantic Schemas (US-06 & US-07)
# ==============================================================================
class CodeExtraction(BaseModel):
    """Extracts runnable Python code from a student's natural-language message."""
    python_code: str = Field(
        description="The exact Python code snippet extracted from the student's message. Empty string if no code was provided."
    )


class GradingResult(BaseModel):
    """Structured grading output required by the Sprints Assessor rubric."""
    score: int = Field(
        ge=0, le=100,
        description="Numeric score from 0 to 100 based on correctness, execution output, and code clarity."
    )
    feedback_points: List[str] = Field(
        description="Concrete, actionable bullet points explaining what worked and what needs improvement."
    )
    pass_status: bool = Field(
        description="True if score >= 70 and code executes without critical runtime errors; False otherwise."
    )


class JudgeEvaluation(BaseModel):
    """LLM-as-a-Judge rubric check for the Evaluator-Optimizer loop."""
    approved: bool = Field(
        description="True if the grade and feedback fairly and accurately match the code and REPL execution output."
    )
    critique: str = Field(
        description="If not approved, specific instructions on how the Grader must adjust the score or feedback."
    )


# ==============================================================================
# 2. Initialize Structured LLMs
# ==============================================================================
base_llm = get_llm(temperature=0)  # Deterministic output for grading and evaluation

extractor_llm = base_llm.with_structured_output(CodeExtraction)
grader_llm = base_llm.with_structured_output(GradingResult)
judge_llm = base_llm.with_structured_output(JudgeEvaluation)


# ==============================================================================
# 3. Assessor Subgraph Nodes
# ==============================================================================
import re

def extract_and_run_code_node(state: OrchestratorState) -> dict:
    """
    Extract the student's complete Python code (including function definitions)
    from their latest message and execute it via PythonREPL.
    """
    last_human_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_human_msg = msg.content
            break

    # 1. Fast 0ms extraction if fenced with ```python ... ```
    fenced = re.search(r"```(?:python)?\s*(.*?)```", last_human_msg, re.DOTALL | re.IGNORECASE)
    if fenced:
        code = fenced.group(1).strip()
    else:
        # 2. Fallback to LLM extractor with explicit instruction to keep ALL lines
        extraction: CodeExtraction = extractor_llm.invoke([
            SystemMessage(
                content=(
                    "Extract the COMPLETE Python program from the user's message verbatim, "
                    "preserving all 'def' function definitions, indentation, newlines, and 'print' statements. "
                    "Do not omit function headers."
                )
            ),
            HumanMessage(content=last_human_msg),
        ])
        code = extraction.python_code.strip()

    if not code:
        repl_output = "Unable to verify: No Python code snippet detected in the student's message."
    else:
        repl_output = execute_student_code.invoke({"code": code})

    print(f"[Assessor Extracted Code]\n{code}\n")
    print(f"[Assessor REPL Trace] {repl_output}")
    return {
        "code_submission": code,
        "retrieved_context": repl_output,
        "iteration_count": 0,
        "judge_feedback": "",
    }

def grader_node(state: OrchestratorState) -> dict:
    """
    Grade the student's Python submission using actual REPL execution results
    and any prior critique from the LLM-as-a-Judge node.
    """
    iteration = state.get("iteration_count", 0) + 1
    code = state.get("code_submission", "")
    repl_output = state.get("retrieved_context", "")
    prior_critique = state.get("judge_feedback", "")

    system_prompt = (
        "You are the Sprints Technical Assessor Agent. Grade the student's Python code fairly "
        "based on syntax, logic, edge cases, and the live Python REPL execution output.\n"
        "- If REPL output starts with 'Unable to verify', the code failed execution (score must be < 70 and pass_status=False).\n"
        "- Pass threshold is score >= 70."
    )

    user_prompt = (
        f"Student Code:\n```python\n{code}\n```\n\n"
        f"Live Python REPL Result:\n{repl_output}\n"
    )
    if prior_critique:
        user_prompt += f"\nPrevious Judge Critique (Refine your grading based on this):\n{prior_critique}\n"

    grade: GradingResult = grader_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    grade_dict = grade.model_dump()
    print(f"[Assessor Grader Trace - Iter {iteration}/{MAX_ITERATIONS}] Score={grade.score}, Pass={grade.pass_status}")

    return {
        "grade_result": grade_dict,
        "iteration_count": iteration,
    }


def judge_node(state: OrchestratorState) -> dict:
    """
    Secondary 'LLM-as-a-Judge' node that audits the Grader's structured output
    against the student's code and REPL output before returning to the student.
    """
    code = state.get("code_submission", "")
    repl_output = state.get("retrieved_context", "")
    grade_dict = state.get("grade_result", {})

    judge_prompt = (
        "You are a senior Sprints Technical Lead auditing an AI Grader's assessment.\n"
        "Verify that:\n"
        "1. The numeric score (0-100) matches pass_status (pass_status MUST be True iff score >= 70).\n"
        "2. If REPL reported an error ('Unable to verify'), the student did NOT pass.\n"
        "3. Feedback points are specific, accurate, and constructive.\n"
        "Approve only if all 3 checks pass."
    )

    evaluation: JudgeEvaluation = judge_llm.invoke([
        SystemMessage(content=judge_prompt),
        HumanMessage(
            content=(
                f"Code:\n{code}\n\n"
                f"REPL Output:\n{repl_output}\n\n"
                f"Proposed Grade JSON:\n{json.dumps(grade_dict, indent=2)}"
            )
        ),
    ])

    print(f"[Assessor Judge Trace] Approved={evaluation.approved} | Critique={evaluation.critique}")
    return {
        "judge_feedback": "" if evaluation.approved else evaluation.critique,
    }


def should_refine(state: OrchestratorState) -> str:
    """
    Conditional edge controlling the Evaluator-Optimizer loop.
    Strictly halts after MAX_ITERATIONS (3) to control token cost and latency.
    """
    critique = state.get("judge_feedback", "")
    iterations = state.get("iteration_count", 0)

    if critique and iterations < MAX_ITERATIONS:
        return "refine"
    return "finalize"


def format_grade_response_node(state: OrchestratorState) -> dict:
    """Format the verified Pydantic grade JSON into a clean AIMessage for the student."""
    grade = state.get("grade_result", {})
    iterations = state.get("iteration_count", 1)

    formatted_json = json.dumps(grade, indent=2)
    reply = (
        f"### Python Assessment Result (Verified in {iterations} pass(es))\n"
        f"```json\n{formatted_json}\n```"
    )
    return {"messages": [AIMessage(content=reply)]}


# ==============================================================================
# 4. Compile the Assessor Subgraph
# ==============================================================================
def build_assessor_subgraph():
    """Build and compile the Evaluator-Optimizer subgraph for the Assessor Agent."""
    sub = StateGraph(OrchestratorState)

    sub.add_node("extract_and_run", extract_and_run_code_node)
    sub.add_node("grader", grader_node)
    sub.add_node("judge", judge_node)
    sub.add_node("format_response", format_grade_response_node)

    sub.set_entry_point("extract_and_run")
    sub.add_edge("extract_and_run", "grader")
    sub.add_edge("grader", "judge")
    sub.add_conditional_edges(
        "judge",
        should_refine,
        {
            "refine": "grader",
            "finalize": "format_response",
        },
    )
    sub.add_edge("format_response", END)

    return sub.compile()


assessor_subgraph = build_assessor_subgraph()


# Quick standalone test
if __name__ == "__main__":
    print("=== TEST A: Valid Code Submission ===")
    res_good = assessor_subgraph.invoke({
        "messages": [HumanMessage(content="Please grade my factorial function:\ndef fact(n):\n    return 1 if n <= 1 else n * fact(n-1)\nprint(fact(5))")]
    })
    print(res_good["messages"][-1].content)

    print("\n=== TEST B: Runtime Error Submission ===")
    res_bad = assessor_subgraph.invoke({
        "messages": [HumanMessage(content="Grade this:\ndef div(a, b):\n    return a / b\nprint(div(10, 0))")]
    })
    print(res_bad["messages"][-1].content)