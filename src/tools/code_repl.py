from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

# Initialize a single PythonREPL instance
repl = PythonREPL()

# Common Python exception prefixes returned as strings by PythonREPL.run()
ERROR_MARKERS = (
    "Traceback (most recent call last):",
    "SyntaxError",
    "IndentationError",
    "NameError",
    "TypeError",
    "ValueError",
    "ZeroDivisionError",
    "IndexError",
    "KeyError",
    "AttributeError",
    "ImportError",
    "RuntimeError",
)


@tool
def execute_student_code(code: str) -> str:
    """
    Execute a student-submitted Python code snippet inside a Python REPL environment
    for the Sprints Assessor Agent and capture its standard output (stdout) or runtime errors.

    Args:
        code: The raw Python code snippet submitted by the student for grading.

    Returns:
        str: Captured stdout output on successful execution, or a structured
             'Unable to verify: ...' message if a syntax or runtime error occurs.
    """
    if not code or not code.strip():
        return "Unable to verify: Empty Python code submission."

    try:
        output = repl.run(code).strip()

        # PythonREPL catches exceptions and returns them as strings rather than raising
        if any(marker in output for marker in ERROR_MARKERS):
            return f"Unable to verify: Code execution failed with error -> {output}"

        if not output:
            return "Code executed successfully with no printed output (stdout was empty)."

        return f"Execution Output (stdout):\n{output}"

    except Exception as e:
        return f"Unable to verify: Python REPL execution failed ({str(e)})."