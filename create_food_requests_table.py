import sqlite3

DB_PATH = 'database/app.db'

def create_food_requests_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT,
            food_type TEXT,
            quantity TEXT,
            pickup_location TEXT,
            pickup_lat REAL,
            pickup_lon REAL,
            pickup_time TEXT,
            status TEXT,
            assigned_volunteer_id INTEGER,
            ngo_id INTEGER,
            completed_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("food_requests table created or already exists.")

if __name__ == "__main__":
    create_food_requests_table()
