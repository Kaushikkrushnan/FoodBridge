"""
Initialize sessions table in the database
Run this script to add the sessions table and session_id column to users table
"""
from database.models import create_auth_tables
from db import get_auth_db_connection
import sqlite3

def init_sessions():
    """Initialize sessions table and add session_id column to users"""
    print("Initializing sessions table...")
    
    # Create auth tables (includes sessions table)
    create_auth_tables()
    
    # Verify sessions table exists
    conn = get_auth_db_connection()
    cursor = conn.cursor()
    
    # Check if sessions table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='sessions'
    """)
    
    if cursor.fetchone():
        print("✅ Sessions table created successfully!")
    else:
        print("❌ Sessions table creation failed!")
    
    # Check if current_session_id column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'current_session_id' in columns:
        print("✅ current_session_id column added to users table!")
    else:
        print("⚠️  current_session_id column not found in users table")
    
    conn.close()
    print("\n✅ Session management initialized successfully!")

if __name__ == '__main__':
    init_sessions()

