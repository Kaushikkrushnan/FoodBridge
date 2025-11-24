import sqlite3

DB_PATH = 'database/app.db'

def add_created_at_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Add created_at column if it doesn't exist
    cursor.execute("PRAGMA table_info(food_requests)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'created_at' not in columns:
        cursor.execute("ALTER TABLE food_requests ADD COLUMN created_at TEXT")
        print("Added 'created_at' column to food_requests table.")
    else:
        print("'created_at' column already exists.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_created_at_column()
