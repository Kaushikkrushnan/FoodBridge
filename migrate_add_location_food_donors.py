"""
Migration script to add lat and lon columns to food_donors table.
"""
import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'app.db')


def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(food_donors)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'lat' not in columns:
        print("Adding 'lat' column to food_donors table...")
        cursor.execute("ALTER TABLE food_donors ADD COLUMN lat REAL")
    else:
        print("'lat' column already exists")
    
    if 'lon' not in columns:
        print("Adding 'lon' column to food_donors table...")
        cursor.execute("ALTER TABLE food_donors ADD COLUMN lon REAL")
    else:
        print("'lon' column already exists")
    
    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
