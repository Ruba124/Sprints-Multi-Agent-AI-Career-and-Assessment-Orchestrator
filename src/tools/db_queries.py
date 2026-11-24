import os
import sqlite3
from langchain_core.tools import tool

# Always resolve path from project root so it works whether called from main.py or notebooks/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "sprints_learner.db")


@tool
def query_learner_db(sql_query: str) -> str:
    """
    Query the Sprints learner SQLite database to retrieve a student's completed modules,
    target salary in EGP, and preferred Egyptian employers.

    Database Schema:
    Table 'learners':
      -- REPLACE THESE WITH THE EXACT COLUMN NAMES PRINTED BY data/setup_db.py --
      - learner_id (TEXT/INTEGER): Unique student identifier
      - name (TEXT): Student full name
      - completed_modules (TEXT): Modules completed in the Sprints bootcamp
      - target_salary_egp (INTEGER/REAL): Student's target salary in EGP
      - preferred_employers (TEXT): Preferred Egyptian tech employers (e.g., Fawry, Paymob)

    Args:
        sql_query: A valid read-only SQLite SELECT query to retrieve learner records.

    Returns:
        str: Formatted query results with column headers, or an 'Unable to verify' message on failure.
    """
    cleaned_query = sql_query.strip()
    if not cleaned_query.upper().startswith("SELECT"):
        return "Unable to verify: Only read-only SELECT queries are permitted on the learner database."

    try:
        if not os.path.exists(DB_PATH):
            return f"Unable to verify: Learner database not found at {DB_PATH}."

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(cleaned_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

        if not rows:
            return "Unable to verify: No matching student records found for that query."

        return f"Columns: {columns}\nRows: {rows}"

    except Exception as e:
        return f"Unable to verify: Database query failed ({str(e)})."