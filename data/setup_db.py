import os
import sqlite3
import pandas as pd

# Resolve paths relative to the repository root so it works from anywhere
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "data", "sprints_learner_db-csv.csv")
db_path = os.path.join(BASE_DIR, "data", "sprints_learner.db")

# 1. Load the CSV with pandas
df = pd.read_csv(csv_path)

# 2. Inspect exact column names, data types, and sample rows
print("Exact Column Names:", df.columns.tolist())
print("\nData Types:\n", df.dtypes)
print("\nFirst 3 Rows:\n", df.head(3))

# 3. Write the DataFrame into a SQLite table named 'learners'
with sqlite3.connect(db_path) as conn:
    df.to_sql("learners", conn, if_exists="replace", index=False)

print(f"\n✓ Saved {len(df)} rows into '{db_path}' (table: 'learners')")