import sqlite3

def add_phone_column():
    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE food_donors ADD COLUMN phone TEXT")
        print("Phone column added to food_donors table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print("Phone column already exists in food_donors table.")
        else:
            print(f"Error adding phone column: {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_phone_column()
