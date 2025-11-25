import sqlite3

DB_PATH = 'database/assignment.db'

ALTERS = [
    "ALTER TABLE food_donor_requests ADD COLUMN volunteer_id INTEGER;",
    "ALTER TABLE food_donor_requests ADD COLUMN volunteer_name TEXT;",
    "ALTER TABLE food_donor_requests ADD COLUMN volunteer_allocated_time TIMESTAMP;"
]

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for sql in ALTERS:
        try:
            cursor.execute(sql)
            print(f"Executed: {sql}")
        except sqlite3.OperationalError as e:
            print(f"Skipped: {sql} (reason: {e})")
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
