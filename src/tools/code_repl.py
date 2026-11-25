import io
import contextlib
from langchain_core.tools import tool


@tool
def execute_student_code(code: str) -> str:
    """
    Execute a student-submitted Python code snippet for the Sprints Assessor Agent
    and capture its standard output (stdout) or runtime errors.

    Args:
        code: The raw Python code snippet submitted by the student for grading.

    Returns:
        str: Captured stdout output on successful execution, or a structured
             'Unable to verify: ...' message if a syntax or runtime error occurs.
    """
    if not code or not code.strip():
        return "Unable to verify: Empty Python code submission."

    stdout_buffer = io.StringIO()
    # Using the exact same dict for globals and locals ensures recursive functions
    # (like `def fact(n): ... fact(n-1)`) can find themselves in global scope.
    shared_scope = {"__builtins__": __builtins__}

    try:
        with contextlib.redirect_stdout(stdout_buffer):
            exec(code, shared_scope, shared_scope)

        output = stdout_buffer.getvalue().strip()
        if not output:
            return "Code executed successfully with no printed output (stdout was empty)."

        return f"Execution Output (stdout):\n{output}"

    except Exception as e:
        return f"Unable to verify: Code execution failed with error -> {type(e).__name__}('{e}')"