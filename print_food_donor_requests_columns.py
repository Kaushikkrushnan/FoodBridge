import sqlite3

DB_PATH = 'database/assignment.db'

def print_food_donor_requests_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(food_donor_requests);")
    columns = cursor.fetchall()
    print("Columns in food_donor_requests:")
    for col in columns:
        print(f"{col[1]} ({col[2]})")
    conn.close()

if __name__ == "__main__":
    print_food_donor_requests_columns()
