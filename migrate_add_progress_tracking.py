"""
Migration to add progress tracking columns to food_donor_requests table.
Adds timestamps for each progress step:
- food_ready_at: When donor marks food as packed and ready
- collected_at: When volunteer collects the food
- near_ngo_at: When volunteer is near NGO
- delivered_at: When delivery is confirmed
"""
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'assignment.db')
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(food_donor_requests)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    print(f"Existing columns: {existing_columns}")
    
    # Add progress tracking columns if they don't exist
    columns_to_add = [
        ('food_ready_at', 'TIMESTAMP'),
        ('collected_at', 'TIMESTAMP'),
        ('near_ngo_at', 'TIMESTAMP'),
        ('delivered_at', 'TIMESTAMP'),
        ('volunteer_phone', 'TEXT'),
        ('updated_at', 'TIMESTAMP')
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE food_donor_requests ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"Column {col_name} might already exist: {e}")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
