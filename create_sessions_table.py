"""
Create sessions table in existing database
Run this to add session management to your existing database
"""
import sqlite3
import os

# Database path
AUTH_DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'auth.db')

def create_sessions_table():
    """Create sessions table and add session_id column to users table"""
    print("Creating sessions table...")
    
    if not os.path.exists(AUTH_DATABASE):
        print(f"[ERROR] Database not found at {AUTH_DATABASE}")
        print("Please make sure the database exists first.")
        return
    
    conn = sqlite3.connect(AUTH_DATABASE)
    cursor = conn.cursor()
    
    try:
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                user_type TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("[OK] Sessions table created!")
        
        # Check if current_session_id column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'current_session_id' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN current_session_id TEXT')
            print("[OK] Added current_session_id column to users table!")
        else:
            print("[OK] current_session_id column already exists in users table")
        
        conn.commit()
        print("\n[OK] Session management setup complete!")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_sessions_table()

