import sqlite3

DB_PATH = 'database/assignment.db'

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE ngo_assignments ADD COLUMN acceptance_time TIMESTAMP;")
        print("Column 'acceptance_time' added to ngo_assignments table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Column 'acceptance_time' already exists.")
        else:
            print(f"Error: {e}")
    conn.commit()
