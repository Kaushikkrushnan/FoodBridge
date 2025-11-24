import sqlite3

DB_PATH = 'database/app.db'
TABLE = 'food_donors'
COLUMN = 'phone'


def ensure_phone_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if column exists
    cursor.execute(f"PRAGMA table_info({TABLE})")
    columns = [row[1] for row in cursor.fetchall()]
    if COLUMN not in columns:
        cursor.execute(f"ALTER TABLE {TABLE} ADD COLUMN {COLUMN} TEXT")
        print(f"Added column '{COLUMN}' to '{TABLE}' table.")
    else:
        print(f"Column '{COLUMN}' already exists in '{TABLE}' table.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    ensure_phone_column()
