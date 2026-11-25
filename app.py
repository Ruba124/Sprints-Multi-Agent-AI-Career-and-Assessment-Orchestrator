# import os
# import sys
# import json
# import time
# import uuid
# import streamlit as st
# from langchain_core.messages import HumanMessage
# from langgraph.types import Command

# # Ensure project root and src/ are importable
# ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
# SRC_DIR = os.path.join(ROOT_DIR, "src")
# for path in (ROOT_DIR, SRC_DIR):
#     if path not in sys.path:
#         sys.path.insert(0, path)

# from main import app as orchestrator_app

# # --- Page Configuration ---
# st.set_page_config(
#     page_title="Sprints Orchestrator — Career & Assessment Studio",
#     page_icon="🧭",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# # --- Session State Initialization ---
# if "thread_id" not in st.session_state:
#     st.session_state.thread_id = f"spr-{uuid.uuid4().hex[:6]}"
# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "pending_hitl" not in st.session_state:
#     st.session_state.pending_hitl = None
# if "last_telemetry" not in st.session_state:
#     st.session_state.last_telemetry = {
#         "agent": "Awaiting Input",
#         "latency_ms": 0,
#         "learner_id": "SPR-1001",
#         "grading_result": None,
#         "rag_context": None,
#         "hitl_status": "Clear",
#     }
# if "prefill_prompt" not in st.session_state:
#     st.session_state.prefill_prompt = ""


# def reset_workspace():
#     st.session_state.thread_id = f"spr-{uuid.uuid4().hex[:6]}"
#     st.session_state.messages = []
#     st.session_state.pending_hitl = None
#     st.session_state.prefill_prompt = ""
#     st.session_state.last_telemetry = {
#         "agent": "Awaiting Input",
#         "latency_ms": 0,
#         "learner_id": "SPR-1001",
#         "grading_result": None,
#         "rag_context": None,
#         "hitl_status": "Clear",
#     }


# def extract_json_block(text: str):
#     """Safely parse embedded JSON grading result if present in assistant output."""
#     if "```json" in text:
#         try:
#             raw = text.split("```json", 1)[1].split("```", 1)[0].strip()
#             return json.loads(raw)
#         except Exception:
#             return None
#     return None


# def run_orchestrator_turn(prompt_text: str):
#     config = {"configurable": {"thread_id": st.session_state.thread_id}}
#     st.session_state.messages.append({"role": "user", "content": prompt_text})

#     t0 = time.perf_counter()
#     res = orchestrator_app.invoke(
#         {"messages": [HumanMessage(content=prompt_text)]},
#         config=config,
#     )
#     elapsed_ms = int((time.perf_counter() - t0) * 1000)

#     snapshot = orchestrator_app.get_state(config)
#     state_vals = snapshot.values if snapshot else res

#     # Update live telemetry inspector
#     st.session_state.last_telemetry["latency_ms"] = elapsed_ms
#     st.session_state.last_telemetry["agent"] = str(state_vals.get("next_agent", "advisor")).upper()
#     if state_vals.get("learner_id"):
#         st.session_state.last_telemetry["learner_id"] = state_vals.get("learner_id")
#     if state_vals.get("retrieved_context"):
#         st.session_state.last_telemetry["rag_context"] = state_vals.get("retrieved_context")

# #     if snapshot and snapshot.next:
# #         interrupt_payload = snapshot.tasks[0].interrupts[0].value
# #         st.session_state.pending_hitl = interrupt_payload
# #         st.session_state.last_telemetry["hitl_status"] = "Paused — Coach Review"
# #     else:
# #         reply = res["messages"][-1].content
# #         parsed_grade = extract_json_block(reply)
# #         if parsed_grade:
# #             st.session_state.last_telemetry["grading_result"] = parsed_grade
# #         st.session_state.last_telemetry["hitl_status"] = "Completed"
# #         st.session_state.messages.append({"role": "assistant", "content": reply})


# # # ==============================================================================
# # # TOP APPLICATION HEADER BAR
# # # ==============================================================================
# # header_left, header_mid, header_right = st.columns([5, 3, 2], vertical_alignment="center")

# # with header_left:
# #     st.title("Sprints Orchestrator")
# #     st.caption("Autonomous Career Advisory, Curriculum RAG & Live Code Assessment Platform")

# # with header_mid:
# #     m1, m2 = st.columns(2)
# #     m1.metric("Session ID", st.session_state.thread_id)
# #     m2.metric("Active Route", st.session_state.last_telemetry["agent"])

# # with header_right:
# #     if st.button("New Session", type="secondary", use_container_width=True):
# #         reset_workspace()
# #         st.rerun()

# # st.divider()

# # # ==============================================================================
# # # MAIN SPLIT WORKSPACE (65% INTERACTIVE STUDIO | 35% LIVE TELEMETRY INSPECTOR)
# # # ==============================================================================
# # workspace_col, inspector_col = st.columns([1.85, 1.15], gap="large")

# # # ------------------------------------------------------------------------------
# # # LEFT COLUMN: INTERACTIVE ORCHESTRATOR STUDIO
# # # ------------------------------------------------------------------------------
# # with workspace_col:
# #     # Scenario Preset Strip (One-Click Demo Scenarios)
# #     with st.container(border=True):
# #         st.subheader("Quick Scenarios", divider="gray")
# #         p1, p2, p3 = st.columns(3)
# #         with p1:
# #             if st.button("Curriculum & Prerequisites", use_container_width=True):
# #                 st.session_state.prefill_prompt = (
# #                     "I am SPR-1001. What modules and score do I need to apply to Fawry?"
# #                 )
# #         with p2:
# #             if st.button("Tier-1 Placement Approval", use_container_width=True):
# #                 st.session_state.prefill_prompt = (
# #                     "Hi, I'm SPR-1001. Can you approve my placement application to Fawry?"
# #                 )
# #         with p3:
# #             if st.button("Python REPL Assessment", use_container_width=True):
# #                 st.session_state.prefill_prompt = (
# #                     "Grade my Python factorial code:\n```python\ndef fact(n):\n    return 1 if n <= 1 else n * fact(n-1)\nprint(fact(5))\n```"
# #                 )

# #     # Conversation & Evaluation Feed
# #     feed_container = st.container(border=True)
# #     with feed_container:
# #         st.subheader("Workspace Feed", divider="gray")

# #         if not st.session_state.messages and st.session_state.pending_hitl is None:
# #             st.info(
# #                 "Select a scenario above or enter a query below. Requests automatically route between "
# #                 "the **Advisor Agent** (SQLite + ChromaDB RAG + HITL) and the **Assessor Agent** (Python REPL + Judge Loop)."
# #             )

# #         for msg in st.session_state.messages:
# #             with st.chat_message(msg["role"]):
# #                 st.markdown(msg["content"])

# #         # --- Interactive Career Coach HITL Approval Gate (US-04) ---
# #         if st.session_state.pending_hitl is not None:
# #             payload = st.session_state.pending_hitl
# #             st.warning(
# #                 f"**Human-in-the-Loop Escalation Triggered** — Tier-1 Partner Review Required ({payload.get('tier1_partner', 'Partner')})"
# #             )

# #             with st.container(border=True):
# #                 c_a, c_b, c_c = st.columns(3)
# #                 c_a.metric("Learner ID", payload.get("learner_id", "SPR-1001"))
# #                 c_b.metric("Target Partner", payload.get("tier1_partner", "Fawry"))
# #                 c_c.metric("Policy Gate", "Tier-1 HITL")

# #                 st.caption("Learner Record Snapshot")
# #                 st.code(payload.get("db_summary", ""), language="text")

# #                 coach_notes = st.text_input(
# #                     "Career Coach Decision Notes",
# #                     value="Verified learner meets all Tier-1 module and score criteria. Cleared for referral.",
# #                     key="coach_decision_notes",
# #                 )

# #                 btn_approve, btn_reject = st.columns(2)
# #                 config = {"configurable": {"thread_id": st.session_state.thread_id}}

# #                 with btn_approve:
# #                     if st.button("Approve Tier-1 Referral", type="primary", use_container_width=True):
# #                         with st.spinner("Resuming Advisor subgraph with Coach approval..."):
# #                             t0 = time.perf_counter()
# #                             res = orchestrator_app.invoke(
# #                                 Command(resume={"approved": True, "notes": coach_notes}),
# #                                 config=config,
# #                             )
# #                             st.session_state.last_telemetry["latency_ms"] = int((time.perf_counter() - t0) * 1000)
# #                             st.session_state.last_telemetry["hitl_status"] = "Approved by Coach"
# #                             st.session_state.messages.append(
# #                                 {"role": "assistant", "content": res["messages"][-1].content}
# #                             )
# #                             st.session_state.pending_hitl = None
# #                         st.rerun()

# #                 with btn_reject:
# #                     if st.button("Place on Hold / Reject", type="secondary", use_container_width=True):
# #                         with st.spinner("Resuming Advisor subgraph with hold notice..."):
# #                             t0 = time.perf_counter()
# #                             res = orchestrator_app.invoke(
# #                                 Command(
# #                                     resume={
# #                                         "approved": False,
# #                                         "notes": coach_notes or "Please complete pending modules before applying.",
# #                                     }
# #                                 ),
# #                                 config=config,
# #                             )
# #                             st.session_state.last_telemetry["latency_ms"] = int((time.perf_counter() - t0) * 1000)
# #                             st.session_state.last_telemetry["hitl_status"] = "Placed on Hold"
# #                             st.session_state.messages.append(
# #                                 {"role": "assistant", "content": res["messages"][-1].content}
# #                             )
# #                             st.session_state.pending_hitl = None
# #                         st.rerun()

# #     # Input Composer (Supports both quick scenario prefill and custom multi-line code/questions)
# #     with st.form("orchestrator_composer", clear_on_submit=True):
# #         prompt_value = st.text_area(
# #             "Prompt or Python Submission",
# #             value=st.session_state.prefill_prompt,
# #             height=105,
# #             placeholder="Ask about Sprints tracks, Tier-1 hiring partners (Fawry, InstaPay), or paste Python code to evaluate...",
# #         )
# #         submit_col1, submit_col2 = st.columns([4, 1])
# #         with submit_col2:
# #             submitted = st.form_submit_button("Run Agent", type="primary", use_container_width=True)

# #     if submitted and prompt_value.strip():
# #         if st.session_state.pending_hitl is not None:
# #             st.toast("Resolve the pending Career Coach HITL review above before sending a new prompt.")
# #         else:
# #             st.session_state.prefill_prompt = ""
# #             with st.spinner("Orchestrating agents and tools..."):
# #                 run_orchestrator_turn(prompt_value.strip())
# #             st.rerun()


# # # ------------------------------------------------------------------------------
# # # RIGHT COLUMN: LIVE AGENT TELEMETRY & ARTIFACT INSPECTOR
# # # ------------------------------------------------------------------------------
# # with inspector_col:
# #     with st.container(border=True):
# #         st.subheader("Live Orchestration Inspector", divider="gray")

# #         t1, t2 = st.columns(2)
# #         t1.metric("Turn Latency", f"{st.session_state.last_telemetry['latency_ms']} ms")
# #         t2.metric("HITL Gate", st.session_state.last_telemetry["hitl_status"])

# #         tab_eval, tab_context, tab_arch = st.tabs(["Assessment Card", "Retrieved Grounding", "System Pipeline"])

# #         with tab_eval:
# #             grade_data = st.session_state.last_telemetry.get("grading_result")
# #             if grade_data:
# #                 score_val = int(grade_data.get("score", 0))
# #                 passed = bool(grade_data.get("pass_status", False))

# #                 g1, g2 = st.columns(2)
# #                 g1.metric("Verified Score", f"{score_val} / 100")
# #                 g2.metric("Status", "PASS" if passed else "FAIL")
# #                 st.progress(min(max(score_val, 0), 100) / 100.0)

# #                 st.caption("Structured Feedback Points")
# #                 for point in grade_data.get("feedback_points", []):
# #                     st.write(f"- {point}")
# #             else:
# #                 st.caption("Submit Python code in the workspace to inspect live REPL execution and Pydantic grading metrics.")

# #         with tab_context:
# #             rag_ctx = st.session_state.last_telemetry.get("rag_context")
# #             if rag_ctx:
# #                 st.caption("SQLite Learner Record & ChromaDB Chunks")
# #                 st.text_area("Grounded Context", value=rag_ctx, height=280, disabled=True)
# #             else:
# #                 st.caption("Ask an Advisor or curriculum question to inspect the retrieved SQLite rows and ChromaDB chunks.")

# #         with tab_arch:
# #             st.caption("Active LangGraph Subgraphs & Tools")
# #             st.dataframe(
# #                 [
# #                     {"Component": "Intent Router", "Backend": "Groq LLM + MemorySaver", "Status": "Active"},
# #                     {"Component": "Curriculum RAG", "Backend": "ChromaDB (MiniLM-L6-v2)", "Status": "Ready"},
# #                     {"Component": "Learner DB", "Backend": "SQLite3 (sprints_learner.db)", "Status": "Ready"},
# #                     {"Component": "HITL Escalation", "Backend": "LangGraph interrupt()", "Status": "Armed"},
# #                     {"Component": "Code Assessor", "Backend": "Python REPL + Judge Loop", "Status": "Ready"},
# #                 ],
# #                 use_container_width=True,
# #                 hide_index=True,
# #             )
# """Masar - Sprints AI Career & Code Assessment.

# Streamlit workspace on top of the compiled LangGraph orchestrator in src/main.py.
# Native Streamlit components only (no raw HTML / CSS). Colors come from
# .streamlit/config.toml.
# """

# import ast
# import json
# import os
# import re
# import sys
# import uuid

# import streamlit as st

# # --------------------------------------------------------------------------- #
# # Backend import (path setup follows the backend contract)
# # --------------------------------------------------------------------------- #
# ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
# SRC_DIR = os.path.join(ROOT_DIR, "src")
# for path in (ROOT_DIR, SRC_DIR):
#     if path not in sys.path:
#         sys.path.insert(0, path)

# st.set_page_config(
#     page_title="Masar | Sprints AI Career & Code Assessment",
#     page_icon=":material/school:",
#     layout="wide",
# )

# from langchain_core.messages import HumanMessage  # noqa: E402
# from langgraph.types import Command  # noqa: E402


# @st.cache_resource(show_spinner="Loading the Masar agents...")
# def load_backend():
#     from main import app as orchestrator_app

#     return orchestrator_app


# try:
#     orchestrator_app = load_backend()
# except Exception as exc:  # noqa: BLE001
#     st.error(
#         "The Masar backend could not be loaded. Check that `src/main.py` exports "
#         "`app` and that your API keys and `data/` folders are in place."
#     )
#     st.exception(exc)
#     st.stop()

# # --------------------------------------------------------------------------- #
# # Constants
# # --------------------------------------------------------------------------- #
# PAUSE_STEP = "Career Coach approval (paused)"
# ASSISTANT_AVATAR = ":material/school:"
# USER_AVATAR = ":material/person:"

# DEMOS = [
#     (
#         "Curriculum question",
#         "What does the Sprints curriculum cover, and how is the program structured?",
#     ),
#     (
#         "My placement status",
#         "My learner ID is SPR-1001. Am I on track for placement?",
#     ),
#     (
#         "Fawry placement",
#         "I'm SPR-1001. Can you recommend me for placement at Fawry?",
#     ),
#     (
#         "No ID given",
#         "Am I eligible for a job placement?",
#     ),
#     (
#         "Assess my code",
#         "Please assess my Python solution.\n\n"
#         "Task: write `is_palindrome(s)` that ignores case and non-letters.\n\n"
#         "```python\n"
#         "def is_palindrome(s):\n"
#         "    cleaned = [c.lower() for c in s if c.isalpha()]\n"
#         "    return cleaned == cleaned[::-1]\n\n"
#         "print(is_palindrome('A man, a plan, a canal: Panama'))\n"
#         "print(is_palindrome('Masar'))\n"
#         "```",
#     ),
# ]


# # --------------------------------------------------------------------------- #
# # Session state
# # --------------------------------------------------------------------------- #
# def init_state():
#     defaults = {
#         "thread_id": str(uuid.uuid4()),
#         "history": [],  # chat feed entries
#         "trace": [],  # ordered node names for the current turn
#         "inspector": None,  # state values to show on the right
#         "pending": None,  # interrupt payload while waiting for the coach
#         "queued_prompt": None,
#         "queued_resume": None,
#     }
#     for key, value in defaults.items():
#         st.session_state.setdefault(key, value)


# def reset_session():
#     st.session_state.thread_id = str(uuid.uuid4())
#     st.session_state.history = []
#     st.session_state.trace = []
#     st.session_state.inspector = None
#     st.session_state.pending = None
#     st.session_state.queued_prompt = None
#     st.session_state.queued_resume = None


# init_state()


# # --------------------------------------------------------------------------- #
# # Callbacks (they run before the script reruns)
# # --------------------------------------------------------------------------- #
# def queue_prompt(text):
#     if text and text.strip():
#         st.session_state.queued_prompt = text.strip()


# def submit_prompt():
#     queue_prompt(st.session_state.get("prompt_text", ""))


# def pick_demo():
#     label = st.session_state.get("demo_pick")
#     for demo_label, prompt in DEMOS:
#         if demo_label == label:
#             queue_prompt(prompt)
#     st.session_state.demo_pick = None


# def resolve(approved):
#     st.session_state.queued_resume = {
#         "approved": approved,
#         "notes": st.session_state.get("coach_notes", "").strip(),
#     }


# # --------------------------------------------------------------------------- #
# # Helpers
# # --------------------------------------------------------------------------- #
# def text_of(content):
#     if isinstance(content, str):
#         return content
#     if isinstance(content, list):
#         parts = []
#         for part in content:
#             if isinstance(part, str):
#                 parts.append(part)
#             elif isinstance(part, dict) and part.get("type") == "text":
#                 parts.append(part.get("text", ""))
#         return "\n".join(parts)
#     return str(content)


# def last_ai_reply(state_vals):
#     for message in reversed(state_vals.get("messages", []) or []):
#         if getattr(message, "type", "") != "human":
#             reply = text_of(message.content)
#             if reply.strip():
#                 return reply
#     return ""


# def get_pending(snapshot):
#     """Return the interrupt payload if the graph is paused, else None."""
#     if snapshot and snapshot.next:
#         try:
#             return snapshot.tasks[0].interrupts[0].value
#         except (IndexError, AttributeError):
#             return None
#     return None


# def node_label(namespace, node):
#     prefix = ""
#     if namespace:
#         prefix = " / ".join(segment.split(":")[0] for segment in namespace) + " / "
#     return prefix + node


# def parse_assessment(text):
#     """Pull the grader's JSON block out of the assessor's final message."""
#     match = re.search(r"```json\s*(\{.*?\})\s*```", text or "", re.DOTALL)
#     raw = match.group(1) if match else None
#     if raw is None:
#         match = re.search(r"\{.*\}", text or "", re.DOTALL)
#         raw = match.group(0) if match else None
#     if raw is None:
#         return None
#     try:
#         data = json.loads(raw)
#         score = int(data.get("score", 0))
#     except (ValueError, TypeError):
#         return None
#     points = [str(p) for p in data.get("feedback_points", []) or []]
#     passed = bool(data.get("pass_status", score >= 70))
#     return {"score": max(0, min(100, score)), "points": points, "passed": passed}


# def split_chunks(text):
#     if not text or not text.strip():
#         return []
#     parts = re.split(r"\n\s*(?:-{3,}|={3,})\s*\n", text)
#     return [p.strip() for p in parts if p.strip()]


# def build_dot(trace, paused):
#     """Graphviz DOT for the ordered node sequence of the current turn."""
#     lines = [
#         "digraph G {",
#         "rankdir=TB;",
#         'bgcolor="transparent";',
#         "nodesep=0.25; ranksep=0.35;",
#         'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, '
#         'color="#0052CC", fillcolor="#F8FAFC", fontcolor="#0F172A", penwidth=1.2];',
#         'edge [color="#64748B", arrowsize=0.7];',
#         'start [label="Your message", shape=oval, fillcolor="#0052CC", '
#         'fontcolor="#FFFFFF"];',
#     ]
#     previous = "start"
#     for index, step in enumerate(trace, start=1):
#         node_id = f"n{index}"
#         label = f"{index}. {step}".replace('"', '\\"')
#         if step == PAUSE_STEP:
#             lines.append(
#                 f'{node_id} [label="{label}", style="rounded,dashed,filled", '
#                 'fillcolor="#FFFFFF"];'
#             )
#         else:
#             lines.append(f'{node_id} [label="{label}"];')
#         lines.append(f"{previous} -> {node_id};")
#         previous = node_id
#     if not paused:
#         lines.append(
#             'end [label="Reply", shape=oval, fillcolor="#0052CC", fontcolor="#FFFFFF"];'
#         )
#         lines.append(f"{previous} -> end;")
#     lines.append("}")
#     return "\n".join(lines)


# # --------------------------------------------------------------------------- #
# # Backend execution
# # --------------------------------------------------------------------------- #
# def run_turn(payload, status):
#     """Run (or resume) the graph, recording each node as it finishes.

#     Uses stream(stream_mode="updates", subgraphs=True) on the same compiled
#     graph and config as invoke(), so the UI can show the exact node order.
#     The final answer is read from get_state(), as in the invoke() contract.
#     """
#     config = {"configurable": {"thread_id": st.session_state.thread_id}}

#     for chunk in orchestrator_app.stream(
#         payload, config=config, stream_mode="updates", subgraphs=True
#     ):
#         if isinstance(chunk, tuple) and len(chunk) == 2:
#             namespace, update = chunk
#         else:
#             namespace, update = (), chunk
#         if not isinstance(update, dict):
#             continue
#         for node in update:
#             if node == "__interrupt__":
#                 step = PAUSE_STEP
#             else:
#                 step = node_label(namespace, node)
#             st.session_state.trace.append(step)
#             status.write(f"Finished **{step}**")

#     snapshot = orchestrator_app.get_state(config)
#     state_vals = snapshot.values if snapshot else {}
#     pending = get_pending(snapshot)
#     route = state_vals.get("next_agent")

#     st.session_state.pending = pending
#     st.session_state.inspector = {
#         "next_agent": route,
#         "needs_identity_prompt": bool(state_vals.get("needs_identity_prompt")),
#         "learner_id": state_vals.get("learner_id"),
#         "db_context": state_vals.get("db_context") or "",
#         "rag_context": state_vals.get("rag_context") or "",
#         "retrieved_context": state_vals.get("retrieved_context") or "",
#         "rag_retries": int(state_vals.get("rag_retries") or 0),
#         "reply": last_ai_reply(state_vals),
#     }

#     if pending:
#         st.session_state.history.append(
#             {
#                 "role": "assistant",
#                 "content": (
#                     "This is a Tier-1 placement question, so a Career Coach needs to "
#                     "review it first. You'll get your answer once they decide."
#                 ),
#                 "route": route,
#             }
#         )
#         status.update(label="Waiting for the Career Coach", state="complete", expanded=False)
#     else:
#         st.session_state.history.append(
#             {
#                 "role": "assistant",
#                 "content": st.session_state.inspector["reply"] or "(No reply returned.)",
#                 "route": route,
#             }
#         )
#         status.update(label="Done", state="complete", expanded=False)


# def execute(payload):
#     with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
#         with st.status("Working on it...", expanded=True) as status:
#             try:
#                 run_turn(payload, status)
#             except Exception as exc:  # noqa: BLE001
#                 status.update(label="Something went wrong", state="error")
#                 st.session_state.history.append(
#                     {"role": "assistant", "content": f"The request failed: {exc}", "error": True}
#                 )


# # --------------------------------------------------------------------------- #
# # Rendering
# # --------------------------------------------------------------------------- #
# def render_message(message):
#     role = message["role"]
#     if role == "coach":
#         with st.chat_message("user", avatar=":material/verified_user:"):
#             st.caption("Career Coach")
#             st.markdown(message["content"])
#     elif role == "assistant":
#         with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
#             if message.get("error"):
#                 st.error(message["content"])
#             else:
#                 st.markdown(message["content"])
#             if message.get("route"):
#                 st.badge(
#                     f"{message['route'].title()} agent",
#                     icon=":material/smart_toy:",
#                     color="blue",
#                 )
#     else:
#         with st.chat_message("user", avatar=USER_AVATAR):
#             st.markdown(message["content"])


# def render_welcome():
#     with st.container(border=True):
#         st.subheader("What can Masar help you with?")
#         st.markdown(
#             "- :material/menu_book: **Curriculum.** Ask what you'll learn and how the program works.\n"
#             "- :material/badge: **Placement.** Check your status with your Learner ID. "
#             "Tier-1 partners go to a Career Coach for approval.\n"
#             "- :material/code: **Code assessment.** Paste a task and your solution to get a score "
#             "and feedback."
#         )
#         st.caption("Pick a demo above or type your own message below.")


# def render_hitl(payload):
#     with st.container(border=True):
#         st.subheader(":material/gavel: Career Coach review")
#         st.caption(
#             payload.get("instruction", "Approve or reject Tier-1 placement recommendation.")
#         )
#         col_partner, col_learner = st.columns(2)
#         col_partner.metric("Tier-1 partner", payload.get("tier1_partner", "Unknown"), border=True)
#         learner = payload.get("learner_id", "Unknown")
#         col_learner.metric("Learner", learner, border=True)
#         if learner == "Unverified Guest":
#             st.warning("This learner has not been verified. Confirm who they are before approving.")
#         st.markdown("**Learner's question**")
#         st.write(payload.get("student_query", ""))
#         with st.expander("Learner record summary", expanded=True):
#             st.text(payload.get("db_summary") or "No database summary was provided.")
#         with st.form("hitl_form", border=False):
#             st.text_area(
#                 "Notes for the learner (optional)",
#                 key="coach_notes",
#                 height=90,
#                 placeholder="Add context the learner should see with the decision.",
#             )
#             col_approve, col_reject = st.columns(2)
#             col_approve.form_submit_button(
#                 "Approve placement",
#                 type="primary",
#                 icon=":material/check_circle:",
#                 on_click=resolve,
#                 args=(True,),
#             )
#             col_reject.form_submit_button(
#                 "Reject placement",
#                 icon=":material/cancel:",
#                 on_click=resolve,
#                 args=(False,),
#             )


# def render_curriculum(inspector):
#     if inspector["needs_identity_prompt"]:
#         st.info(
#             "The agent asked for a Learner ID (SPR-XXXX) or name before it looks up "
#             "personal records."
#         )
#     retries = max(0, min(inspector["rag_retries"], 2))
#     st.progress(retries / 2, text=f"Self-reflection query rewrites: {retries} of 2")

#     retrieved = inspector["retrieved_context"] or inspector["rag_context"]
#     chunks = split_chunks(retrieved)
#     if chunks:
#         st.caption(f"{len(chunks)} chunk(s) retrieved from sprints_curriculum.md")
#         for number, chunk in enumerate(chunks, start=1):
#             with st.container(border=True):
#                 st.badge(f"Chunk {number}", icon=":material/article:", color="gray")
#                 st.markdown(chunk)
#     else:
#         st.caption("No curriculum chunks were retrieved this turn.")

#     rag = inspector["rag_context"]
#     retrieved_raw = inspector["retrieved_context"]
#     if retrieved_raw and rag and rag.strip() != retrieved_raw.strip():
#         with st.expander("Context passed to the answer"):
#             st.markdown(rag)


# def render_learner(inspector):
#     db_context = inspector["db_context"].strip()
#     if not db_context:
#         st.caption("No learner database lookup was needed for this question.")
#         return
#     rows = None
#     try:
#         parsed = ast.literal_eval(db_context)
#         if isinstance(parsed, list) and parsed and isinstance(parsed[0], (tuple, list, dict)):
#             rows = parsed
#     except (ValueError, SyntaxError):
#         rows = None
#     if rows is not None:
#         st.caption(f"{len(rows)} row(s) returned from data/sprints_learner.db")
#         st.dataframe(rows)
#     else:
#         st.caption("Raw result from data/sprints_learner.db")
#         st.code(db_context, language="text")


# def render_assessment(inspector):
#     assessment = parse_assessment(inspector["reply"])
#     if assessment is None:
#         st.caption("The assessor has not returned a score for this turn.")
#         return
#     with st.container(border=True):
#         st.progress(assessment["score"] / 100, text=f"Score {assessment['score']} of 100 (pass at 70)")
#         if assessment["passed"]:
#             st.success("This solution meets the passing score.", icon=":material/check_circle:")
#         else:
#             st.warning("This solution is below the passing score of 70.", icon=":material/error:")
#     st.markdown("**Feedback**")
#     if not assessment["points"]:
#         st.caption("No feedback points were returned.")
#     for number, point in enumerate(assessment["points"], start=1):
#         with st.container(border=True):
#             st.badge(f"Point {number}", icon=":material/chat_bubble:", color="blue")
#             st.markdown(point)


# def render_execution():
#     trace = st.session_state.trace
#     st.caption(f"{len(trace)} step(s) ran for this turn, in order.")
#     with st.container(border=True):
#         st.graphviz_chart(build_dot(trace, paused=st.session_state.pending is not None))


# def render_inspector():
#     st.subheader(":material/monitoring: Inspector")
#     inspector = st.session_state.inspector

#     if inspector is None:
#         with st.container(border=True):
#             st.markdown(":material/search_insights: **Nothing to inspect yet**")
#             st.caption(
#                 "Send a message or pick a demo. Retrieved curriculum chunks, learner "
#                 "records, assessment scores and the path the agents took will show up here."
#             )
#         return

#     route = inspector["next_agent"] or "unknown"
#     col_route, col_a, col_b = st.columns(3)
#     col_route.metric("Routed to", route.title(), border=True)
#     if route == "assessor":
#         assessment = parse_assessment(inspector["reply"])
#         col_a.metric("Score", f"{assessment['score']}" if assessment else "-", border=True)
#         col_b.metric(
#             "Result",
#             ("Passed" if assessment["passed"] else "Not yet") if assessment else "-",
#             border=True,
#         )
#         names = [":material/grading: Assessment"]
#     else:
#         col_a.metric("Learner", inspector["learner_id"] or "Not given", border=True)
#         col_b.metric("Query rewrites", inspector["rag_retries"], border=True)
#         names = [":material/menu_book: Curriculum", ":material/database: Learner record"]

#     if st.session_state.trace:
#         names.append(":material/account_tree: Execution path")

#     tabs = st.tabs(names)
#     if route == "assessor":
#         with tabs[0]:
#             render_assessment(inspector)
#     else:
#         with tabs[0]:
#             render_curriculum(inspector)
#         with tabs[1]:
#             render_learner(inspector)
#     if st.session_state.trace:
#         with tabs[-1]:
#             render_execution()


# # --------------------------------------------------------------------------- #
# # Page
# # --------------------------------------------------------------------------- #
# with st.sidebar:
#     st.subheader(":material/tune: Session")
#     st.caption("Thread ID")
#     st.code(st.session_state.thread_id, language="text")
#     st.button("Start a new session", icon=":material/add:", on_click=reset_session)

# is_paused = st.session_state.pending is not None

# head_left, head_right = st.columns([4, 1], vertical_alignment="center")
# with head_left:
#     st.title(":material/route: Masar")
#     st.caption("Sprints AI Career & Code Assessment")
# with head_right:
#     if is_paused:
#         st.badge("Awaiting coach", icon=":material/hourglass_top:", color="orange")
#     else:
#         st.badge("Ready", icon=":material/check_circle:", color="green")

# left, right = st.columns([3, 2], gap="large")

# with left:
#     st.pills(
#         "Try a demo",
#         [label for label, _ in DEMOS],
#         key="demo_pick",
#         on_change=pick_demo,
#         disabled=is_paused,
#         label_visibility="collapsed",
#     )

#     feed = st.container(height=540, border=False)
#     with feed:
#         if not st.session_state.history and not (
#             st.session_state.queued_prompt or st.session_state.queued_resume
#         ):
#             render_welcome()

#         for entry in st.session_state.history:
#             render_message(entry)

#         if st.session_state.queued_prompt is not None:
#             text = st.session_state.queued_prompt
#             st.session_state.queued_prompt = None
#             st.session_state.history.append({"role": "user", "content": text})
#             st.session_state.trace = []
#             render_message({"role": "user", "content": text})
#             execute({"messages": [HumanMessage(content=text)]})
#             st.rerun()

#         elif st.session_state.queued_resume is not None:
#             decision = st.session_state.queued_resume
#             st.session_state.queued_resume = None
#             verdict = "Approved" if decision["approved"] else "Rejected"
#             note = f"**{verdict}** the Tier-1 placement recommendation."
#             if decision["notes"]:
#                 note += f"\n\nCoach notes: {decision['notes']}"
#             coach_message = {"role": "coach", "content": note}
#             st.session_state.history.append(coach_message)
#             st.session_state.pending = None
#             render_message(coach_message)
#             execute(Command(resume=decision))
#             st.rerun()

#     if st.session_state.pending is not None:
#         render_hitl(st.session_state.pending)

#     with st.form("prompt_form", clear_on_submit=True, border=True):
#         st.text_area(
#             "Message",
#             key="prompt_text",
#             height=110,
#             disabled=is_paused,
#             label_visibility="collapsed",
#             placeholder="Ask about the curriculum or your placement, or paste a task with your code.",
#         )
#         st.form_submit_button(
#             "Send",
#             type="primary",
#             icon=":material/send:",
#             on_click=submit_prompt,
#             disabled=is_paused,
#         )
#     if is_paused:
#         st.caption("Chat is paused until the Career Coach approves or rejects the placement.")

# with right:
#     render_inspector()

"""Masar - Sprints AI Career & Code Assessment.

Streamlit workspace on top of the compiled LangGraph orchestrator in src/main.py.
Native Streamlit components only (no raw HTML / CSS). Colors come from
.streamlit/config.toml.
"""

import ast
import json
import os
import re
import sys
import uuid

import streamlit as st

# --------------------------------------------------------------------------- #
# Backend import (path setup follows the backend contract)
# --------------------------------------------------------------------------- #
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
for path in (ROOT_DIR, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

st.set_page_config(
    page_title="Masar | Sprints AI Career & Code Assessment",
    page_icon=":material/school:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.types import Command  # noqa: E402


@st.cache_resource(show_spinner="Loading the Masar agents...")
def load_backend():
    from main import app as orchestrator_app

    return orchestrator_app


try:
    orchestrator_app = load_backend()
except Exception as exc:  # noqa: BLE001
    st.error(
        "The Masar backend could not be loaded. Check that `src/main.py` exports "
        "`app` and that your API keys and `data/` folders are in place."
    )
    st.exception(exc)
    st.stop()

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
PAUSE_STEP = "Career Coach approval (paused)"
WATCHED_KEYS = (
    "next_agent",
    "needs_identity_prompt",
    "learner_id",
    "db_context",
    "rag_context",
    "retrieved_context",
    "rag_retries",
)
ASSISTANT_AVATAR = ":material/school:"
USER_AVATAR = ":material/person:"

DEMOS = [
    (
        "Curriculum question",
        "What does the Sprints curriculum cover, and how is the program structured?",
    ),
    (
        "My placement status",
        "My learner ID is SPR-1001. Am I on track for placement?",
    ),
    (
        "Fawry placement",
        "I'm SPR-1001. Can you recommend me for placement at Fawry?",
    ),
    (
        "No ID given",
        "Am I eligible for a job placement?",
    ),
    (
        "Assess my code",
        "Please assess my Python solution.\n\n"
        "Task: write `is_palindrome(s)` that ignores case and non-letters.\n\n"
        "```python\n"
        "def is_palindrome(s):\n"
        "    cleaned = [c.lower() for c in s if c.isalpha()]\n"
        "    return cleaned == cleaned[::-1]\n\n"
        "print(is_palindrome('A man, a plan, a canal: Panama'))\n"
        "print(is_palindrome('Masar'))\n"
        "```",
    ),
]


# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
def init_state():
    defaults = {
        "thread_id": str(uuid.uuid4()),
        "history": [],  # chat feed entries
        "trace": [],  # ordered node names for the current turn
        "turn_updates": {},  # state keys seen in node updates this turn
        "inspector": None,  # state values to show on the right
        "pending": None,  # interrupt payload while waiting for the coach
        "queued_prompt": None,
        "queued_resume": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_session():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.history = []
    st.session_state.trace = []
    st.session_state.turn_updates = {}
    st.session_state.inspector = None
    st.session_state.pending = None
    st.session_state.queued_prompt = None
    st.session_state.queued_resume = None


init_state()


# --------------------------------------------------------------------------- #
# Callbacks (they run before the script reruns)
# --------------------------------------------------------------------------- #
def queue_prompt(text):
    if text and text.strip():
        st.session_state.queued_prompt = text.strip()


def submit_prompt():
    queue_prompt(st.session_state.get("prompt_text", ""))


def pick_demo():
    label = st.session_state.get("demo_pick")
    for demo_label, prompt in DEMOS:
        if demo_label == label:
            queue_prompt(prompt)
    st.session_state.demo_pick = None


def resolve(approved):
    st.session_state.queued_resume = {
        "approved": approved,
        "notes": st.session_state.get("coach_notes", "").strip(),
    }


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return "\n".join(parts)
    return str(content)


def last_ai_reply(state_vals):
    for message in reversed(state_vals.get("messages", []) or []):
        if getattr(message, "type", "") != "human":
            reply = text_of(message.content)
            if reply.strip():
                return reply
    return ""


def get_pending(snapshot):
    """Return the interrupt payload if the graph is paused, else None."""
    if snapshot and snapshot.next:
        try:
            return snapshot.tasks[0].interrupts[0].value
        except (IndexError, AttributeError):
            return None
    return None


def node_label(namespace, node):
    prefix = ""
    if namespace:
        prefix = " / ".join(segment.split(":")[0] for segment in namespace) + " / "
    return prefix + node


def parse_assessment(text):
    """Pull the grader's JSON block out of the assessor's final message."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", text or "", re.DOTALL)
    raw = match.group(1) if match else None
    if raw is None:
        match = re.search(r"\{.*\}", text or "", re.DOTALL)
        raw = match.group(0) if match else None
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        score = int(data.get("score", 0))
    except (ValueError, TypeError):
        return None
    points = [str(p) for p in data.get("feedback_points", []) or []]
    passed = bool(data.get("pass_status", score >= 70))
    return {"score": max(0, min(100, score)), "points": points, "passed": passed}


def split_chunks(text):
    if not text or not text.strip():
        return []
    if "[Chunk" in text:
        pieces = re.split(r"\[Chunk \d+[^\]]*\]", text)
        bodies = []
        for piece in pieces:
            body = re.sub(r"\n\s*Chunk \d+\s*$", "", piece.strip()).strip()
            if body:
                bodies.append(body)
        if bodies:
            return bodies
    parts = re.split(r"\n\s*(?:-{3,}|={3,})\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def find_learner_id(*texts):
    for text in texts:
        if text:
            match = re.search(r"\bSPR-\d+\b", str(text), re.IGNORECASE)
            if match:
                return match.group(0).upper()
    return None


def parse_learner_record(text):
    """Parse 'Columns: [...] Rows: [(...)]' text into a list of dicts."""
    if not text:
        return []
    columns = re.search(r"Columns:\s*(\[[^\]]*\])", text)
    rows = re.search(r"Rows:\s*(\[\(.*?\)\])", text, re.DOTALL)
    if not columns or not rows:
        return []
    try:
        names = ast.literal_eval(columns.group(1))
        values = ast.literal_eval(rows.group(1))
        return [dict(zip(names, row)) for row in values]
    except (ValueError, SyntaxError):
        return []


def build_dot(trace, paused):
    """Graphviz DOT for the ordered node sequence of the current turn."""
    lines = [
        "digraph G {",
        "rankdir=TB;",
        'bgcolor="transparent";',
        "nodesep=0.25; ranksep=0.35;",
        'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, '
        'color="#2F80FF", fillcolor="#0A1224", fontcolor="#EAF2FF", penwidth=1.3];',
        'edge [color="#62D0FF", arrowsize=0.7];',
        'start [label="Your message", shape=oval, fillcolor="#2F80FF", '
        'fontcolor="#FFFFFF"];',
    ]
    previous = "start"
    for index, step in enumerate(trace, start=1):
        node_id = f"n{index}"
        label = f"{index}. {step}".replace('"', '\\"')
        if step == PAUSE_STEP:
            lines.append(
                f'{node_id} [label="{label}", style="rounded,dashed,filled", '
                'fillcolor="#04070D", color="#62D0FF", fontcolor="#62D0FF"];'
            )
        else:
            lines.append(f'{node_id} [label="{label}"];')
        lines.append(f"{previous} -> {node_id};")
        previous = node_id
    if not paused:
        lines.append(
            'end [label="Reply", shape=oval, fillcolor="#2F80FF", fontcolor="#FFFFFF"];'
        )
        lines.append(f"{previous} -> end;")
    lines.append("}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Backend execution
# --------------------------------------------------------------------------- #
def run_turn(payload, status):
    """Run (or resume) the graph, recording each node as it finishes.

    Uses stream(stream_mode="updates", subgraphs=True) on the same compiled
    graph and config as invoke(), so the UI can show the exact node order.
    The final answer is read from get_state(), as in the invoke() contract.
    """
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    for chunk in orchestrator_app.stream(
        payload, config=config, stream_mode="updates", subgraphs=True
    ):
        if isinstance(chunk, tuple) and len(chunk) == 2:
            namespace, update = chunk
        else:
            namespace, update = (), chunk
        if not isinstance(update, dict):
            continue
        for node in update:
            if node == "__interrupt__":
                step = PAUSE_STEP
            else:
                step = node_label(namespace, node)
            st.session_state.trace.append(step)
            status.write(f"Finished **{step}**")
            node_update = update[node]
            if node != "__interrupt__" and isinstance(node_update, dict):
                for key in WATCHED_KEYS:
                    value = node_update.get(key)
                    if value is None or value == "":
                        continue
                    st.session_state.turn_updates[key] = value

    snapshot = orchestrator_app.get_state(config)
    state_vals = snapshot.values if snapshot else {}
    pending = get_pending(snapshot)

    # Subgraph-private keys (learner_id, db_context, ...) are not always exposed on the
    # parent snapshot, so also read the paused subgraph's state and this turn's node updates.
    sub_vals = {}
    try:
        deep = orchestrator_app.get_state(config, subgraphs=True)
        for task in getattr(deep, "tasks", None) or ():
            sub_state = getattr(task, "state", None)
            if sub_state is not None and getattr(sub_state, "values", None):
                sub_vals.update(sub_state.values)
    except Exception:  # noqa: BLE001
        sub_vals = {}

    turn_updates = st.session_state.turn_updates
    sources = {}

    def pick(key):
        for name, source in (
            ("parent state", state_vals),
            ("subgraph state", sub_vals),
            ("node updates", turn_updates),
        ):
            value = source.get(key)
            if value is not None and value != "":
                sources[key] = name
                return value
        return None

    learner_id = pick("learner_id")
    db_context = pick("db_context") or ""
    if pending:
        payload_learner = pending.get("learner_id")
        if not learner_id and payload_learner and payload_learner != "Unverified Guest":
            learner_id = payload_learner
            sources["learner_id"] = "approval request"
        if not db_context and pending.get("db_summary"):
            db_context = pending["db_summary"]
            sources["db_context"] = "approval request"

    # The backend can return the DB record and the curriculum chunks as one text block.
    rag_from_db = ""
    if "=== CURRICULUM RAG ===" in db_context:
        db_context, _, rag_from_db = db_context.partition("=== CURRICULUM RAG ===")
    db_context = db_context.replace("=== LEARNER DB RECORD ===", "").strip()
    rag_from_db = rag_from_db.strip()

    if not learner_id:
        record = parse_learner_record(db_context)
        last_user = next(
            (m["content"] for m in reversed(st.session_state.history) if m["role"] == "user"),
            "",
        )
        learner_id = find_learner_id(
            record[0].get("learner_id") if record else None,
            db_context,
            (pending or {}).get("student_query"),
            last_user,
        )
        if learner_id:
            sources["learner_id"] = "learner record or your message"

    route = pick("next_agent")
    st.session_state.pending = pending
    st.session_state.inspector = {
        "next_agent": route,
        "needs_identity_prompt": bool(pick("needs_identity_prompt")),
        "learner_id": learner_id,
        "db_context": db_context,
        "rag_context": pick("rag_context") or "",
        "retrieved_context": pick("retrieved_context") or rag_from_db,
        "rag_retries": int(pick("rag_retries") or 0),
        "reply": last_ai_reply(state_vals),
        "debug": {
            "parent_state_keys": sorted(state_vals.keys()),
            "subgraph_state_keys": sorted(sub_vals.keys()),
            "node_update_keys": sorted(turn_updates.keys()),
            "value_came_from": sources,
        },
    }

    if pending:
        st.session_state.history.append(
            {
                "role": "assistant",
                "content": (
                    "This is a Tier-1 placement question, so a Career Coach needs to "
                    "review it first. You'll get your answer once they decide."
                ),
                "route": route,
            }
        )
        status.update(label="Waiting for the Career Coach", state="complete", expanded=False)
    else:
        st.session_state.history.append(
            {
                "role": "assistant",
                "content": st.session_state.inspector["reply"] or "(No reply returned.)",
                "route": route,
            }
        )
        status.update(label="Done", state="complete", expanded=False)


def execute(payload):
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.status("Working on it...", expanded=True) as status:
            try:
                run_turn(payload, status)
            except Exception as exc:  # noqa: BLE001
                status.update(label="Something went wrong", state="error")
                st.session_state.history.append(
                    {"role": "assistant", "content": f"The request failed: {exc}", "error": True}
                )


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
DEMO_META = {
    "Curriculum question": (":material/menu_book:", "Ask what the program covers."),
    "My placement status": (":material/badge:", "Check your status with a Learner ID."),
    "Fawry placement": (":material/gavel:", "Sends the request to a Career Coach."),
    "No ID given": (":material/help:", "The agent should ask who you are."),
    "Assess my code": (":material/code:", "Grade a sample Python solution."),
}

PANEL_HEIGHT = 540


def stretch(widget, *args, **kwargs):
    """Full-width widget that works across Streamlit versions."""
    try:
        return widget(*args, width="stretch", **kwargs)
    except TypeError:
        return widget(*args, use_container_width=True, **kwargs)


def stat(column, label, value, icon):
    """Compact stat card that wraps long values instead of truncating them."""
    with column:
        with st.container(border=True):
            st.caption(f"{icon} {label}")
            st.markdown(f"#### {value}")


def render_message(message):
    role = message["role"]
    if role == "coach":
        with st.chat_message("user", avatar=":material/verified_user:"):
            st.caption("Career Coach")
            st.markdown(message["content"])
    elif role == "assistant":
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            if message.get("error"):
                st.error(message["content"])
            else:
                st.markdown(message["content"])
            if message.get("route"):
                st.badge(
                    f"{message['route'].title()} agent",
                    icon=":material/smart_toy:",
                    color="blue",
                )
    else:
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(message["content"])


def render_welcome():
    st.subheader("What can Masar help you with?")
    st.caption("Run a demo to see the agents work, or type your own message below.")
    for start in range(0, len(DEMOS), 2):
        columns = st.columns(2)
        for column, (label, prompt) in zip(columns, DEMOS[start : start + 2]):
            icon, blurb = DEMO_META.get(label, (":material/bolt:", ""))
            with column:
                with st.container(border=True):
                    st.markdown(f"{icon} **{label}**")
                    st.caption(blurb)
                    stretch(
                        st.button,
                        "Run demo",
                        key=f"welcome_{label}",
                        on_click=queue_prompt,
                        args=(prompt,),
                    )


def render_hitl(payload):
    with st.container(border=True):
        st.subheader(":material/gavel: Career Coach review")
        st.caption(
            payload.get("instruction", "Approve or reject Tier-1 placement recommendation.")
        )
        learner = payload.get("learner_id", "Unknown")
        col_partner, col_learner = st.columns(2)
        stat(col_partner, "Tier-1 partner", payload.get("tier1_partner", "Unknown"), ":material/business:")
        stat(col_learner, "Learner", learner, ":material/person:")
        if learner == "Unverified Guest":
            st.warning("This learner has not been verified. Confirm who they are before approving.")
        st.markdown("**Learner's question**")
        st.write(payload.get("student_query", ""))
        with st.expander("Learner record summary", expanded=False):
            st.text(payload.get("db_summary") or "No database summary was provided.")
        with st.form("hitl_form", border=False):
            st.text_area(
                "Notes for the learner (optional)",
                key="coach_notes",
                height=90,
                placeholder="Add context the learner should see with the decision.",
            )
            col_approve, col_reject = st.columns(2)
            with col_approve:
                stretch(
                    st.form_submit_button,
                    "Approve placement",
                    type="primary",
                    icon=":material/check_circle:",
                    on_click=resolve,
                    args=(True,),
                )
            with col_reject:
                stretch(
                    st.form_submit_button,
                    "Reject placement",
                    icon=":material/cancel:",
                    on_click=resolve,
                    args=(False,),
                )


def scroll_area():
    return st.container(height=PANEL_HEIGHT - 60, border=False)


def render_curriculum(inspector):
    if inspector["needs_identity_prompt"]:
        st.info(
            "The agent asked for a Learner ID (SPR-XXXX) or name before it looks up "
            "personal records."
        )
    retries = max(0, min(inspector["rag_retries"], 2))
    st.progress(retries / 2, text=f"Self-reflection query rewrites: {retries} of 2")

    retrieved = inspector["retrieved_context"] or inspector["rag_context"]
    chunks = split_chunks(retrieved)
    if chunks:
        st.caption(f"{len(chunks)} chunk(s) retrieved from sprints_curriculum.md")
        for number, chunk in enumerate(chunks, start=1):
            with st.container(border=True):
                st.badge(f"Chunk {number}", icon=":material/article:", color="blue")
                st.markdown(chunk)
    else:
        st.caption("No curriculum chunks were retrieved this turn.")

    rag = inspector["rag_context"]
    retrieved_raw = inspector["retrieved_context"]
    if retrieved_raw and rag and rag.strip() != retrieved_raw.strip():
        with st.expander("Context passed to the answer"):
            st.markdown(rag)


def render_learner(inspector):
    db_context = inspector["db_context"].strip()
    if not db_context:
        st.caption("No learner database lookup was needed for this question.")
        return
    records = parse_learner_record(db_context)
    if not records:
        st.caption("Raw result from data/sprints_learner.db")
        st.code(db_context, language="text")
        return

    record = records[0]
    salary = record.get("target_salary_egp", "-")
    if isinstance(salary, (int, float)):
        salary = f"{salary:,.0f}"
    with st.container(border=True):
        st.markdown(f"### {record.get('name', 'Learner')}")
        st.caption(f"{record.get('learner_id', '')} | {record.get('bootcamp_track', '')}")
        col_a, col_b = st.columns(2)
        stat(col_a, "Modules completed", record.get("completed_modules", "-"), ":material/library_books:")
        stat(col_b, "Python score", f"{record.get('python_assignment_score', '-')} / 100", ":material/grade:")
        col_c, col_d = st.columns(2)
        stat(col_c, "Target salary (EGP)", salary, ":material/payments:")
        stat(col_d, "Readiness", record.get("readiness_status", "-"), ":material/verified:")
        employers = [
            e.strip() for e in str(record.get("preferred_employers", "")).split(",") if e.strip()
        ]
        if employers:
            st.caption("Preferred employers")
            st.markdown(" ".join(f":blue-badge[{e}]" for e in employers))
    with st.expander("Raw database result"):
        st.code(db_context, language="text")


def render_assessment(inspector):
    assessment = parse_assessment(inspector["reply"])
    if assessment is None:
        st.caption("The assessor has not returned a score for this turn.")
        return
    with st.container(border=True):
        st.progress(
            assessment["score"] / 100,
            text=f"Score {assessment['score']} of 100 (pass at 70)",
        )
        if assessment["passed"]:
            st.success("This solution meets the passing score.", icon=":material/check_circle:")
        else:
            st.warning("This solution is below the passing score of 70.", icon=":material/error:")
    st.markdown("**Feedback**")
    if not assessment["points"]:
        st.caption("No feedback points were returned.")
    for number, point in enumerate(assessment["points"], start=1):
        with st.container(border=True):
            st.badge(f"Point {number}", icon=":material/chat_bubble:", color="blue")
            st.markdown(point)


def render_execution():
    trace = st.session_state.trace
    st.caption(f"{len(trace)} step(s) ran for this turn, in order.")
    with st.container(border=True):
        st.graphviz_chart(build_dot(trace, paused=st.session_state.pending is not None))


def render_inspector():
    st.subheader(":material/monitoring: Inspector")
    inspector = st.session_state.inspector

    if inspector is None:
        with st.container(border=True, height=PANEL_HEIGHT):
            st.markdown("**Nothing to inspect yet**")
            st.caption("Once you send a message, this panel shows:")
            st.markdown(
                "- :material/menu_book: Curriculum chunks the agent retrieved\n"
                "- :material/database: Learner records it looked up\n"
                "- :material/grading: Code scores and feedback\n"
                "- :material/account_tree: The path the agents took"
            )
        return

    route = inspector["next_agent"] or "unknown"
    col_route, col_a, col_b = st.columns(3)
    stat(col_route, "Routed to", route.title(), ":material/alt_route:")
    if route == "assessor":
        assessment = parse_assessment(inspector["reply"])
        stat(col_a, "Score", f"{assessment['score']} / 100" if assessment else "None", ":material/grade:")
        stat(
            col_b,
            "Result",
            ("Passed" if assessment["passed"] else "Not yet") if assessment else "None",
            ":material/task_alt:",
        )
        names = [":material/grading: Assessment"]
    else:
        stat(col_a, "Learner", inspector["learner_id"] or "Not given", ":material/person:")
        stat(col_b, "Rewrites", inspector["rag_retries"], ":material/autorenew:")
        names = [":material/menu_book: Curriculum", ":material/database: Learner record"]

    if st.session_state.trace:
        names.append(":material/account_tree: Execution path")

    tabs = st.tabs(names)
    if route == "assessor":
        with tabs[0]:
            with scroll_area():
                render_assessment(inspector)
    else:
        with tabs[0]:
            with scroll_area():
                render_curriculum(inspector)
        with tabs[1]:
            with scroll_area():
                render_learner(inspector)
    if st.session_state.trace:
        with tabs[-1]:
            with scroll_area():
                render_execution()

    with st.expander(":material/bug_report: Debug: what the UI received"):
        st.caption("Shows which state keys were visible and where each value came from.")
        st.json(inspector.get("debug", {}))


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
is_paused = st.session_state.pending is not None

head_title, head_status, head_menu = st.columns([6, 2, 2], vertical_alignment="center")
with head_title:
    st.title(":material/route: Masar")
    st.caption("Sprints AI Career & Code Assessment")
with head_status:
    if is_paused:
        st.badge("Awaiting coach", icon=":material/hourglass_top:", color="orange")
    else:
        st.badge("Ready", icon=":material/check_circle:", color="green")
with head_menu:
    with st.popover("Session", icon=":material/tune:"):
        st.caption("Thread ID")
        st.caption(st.session_state.thread_id)
        st.button("Start a new session", icon=":material/add:", on_click=reset_session)

left, right = st.columns([3, 2], gap="large")

with left:
    feed = st.container(height=PANEL_HEIGHT, border=True)
    with feed:
        if not st.session_state.history and not (
            st.session_state.queued_prompt or st.session_state.queued_resume
        ):
            render_welcome()

        for entry in st.session_state.history:
            render_message(entry)

        if st.session_state.queued_prompt is not None:
            text = st.session_state.queued_prompt
            st.session_state.queued_prompt = None
            st.session_state.history.append({"role": "user", "content": text})
            st.session_state.trace = []
            st.session_state.turn_updates = {}
            render_message({"role": "user", "content": text})
            execute({"messages": [HumanMessage(content=text)]})
            st.rerun()

        elif st.session_state.queued_resume is not None:
            decision = st.session_state.queued_resume
            st.session_state.queued_resume = None
            verdict = "Approved" if decision["approved"] else "Rejected"
            note = f"**{verdict}** the Tier-1 placement recommendation."
            if decision["notes"]:
                note += f"\n\nCoach notes: {decision['notes']}"
            coach_message = {"role": "coach", "content": note}
            st.session_state.history.append(coach_message)
            st.session_state.pending = None
            render_message(coach_message)
            execute(Command(resume=decision))
            st.rerun()

    if st.session_state.pending is not None:
        render_hitl(st.session_state.pending)

    with st.form("prompt_form", clear_on_submit=True, border=True):
        st.text_area(
            "Message",
            key="prompt_text",
            height=100,
            disabled=is_paused,
            label_visibility="collapsed",
            placeholder="Ask about the curriculum or your placement, or paste a task with your code.",
        )
        col_demo_hint, col_send = st.columns([3, 1], vertical_alignment="center")
        col_demo_hint.caption("Press Ctrl + Enter to send.")
        with col_send:
            stretch(
                st.form_submit_button,
                "Send",
                type="primary",
                icon=":material/send:",
                on_click=submit_prompt,
                disabled=is_paused,
            )

    with st.popover("Demo prompts", icon=":material/bolt:"):
        for label, prompt in DEMOS:
            icon_name = DEMO_META.get(label, (":material/bolt:", ""))[0]
            stretch(
                st.button,
                label,
                key=f"pop_{label}",
                icon=icon_name,
                on_click=queue_prompt,
                args=(prompt,),
                disabled=is_paused,
            )
    if is_paused:
        st.caption("Chat is paused until the Career Coach approves or rejects the placement.")

with right:
    render_inspector()