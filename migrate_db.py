import sqlite3

def migrate_ngos_table():
    """Migrate existing ngos table to remove password and add firebase_uid"""
    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()

    # Check if firebase_uid column exists
    cursor.execute("PRAGMA table_info(ngos)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'firebase_uid' not in columns:
        # Add firebase_uid column (without UNIQUE initially)
        cursor.execute("ALTER TABLE ngos ADD COLUMN firebase_uid TEXT")

    # Remove password column if it exists
    if 'password' in columns:
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        cursor.execute("PRAGMA foreign_keys=off")

        # Drop ngos_new if it exists from previous failed attempt
        cursor.execute("DROP TABLE IF EXISTS ngos_new")

        # Create new table without password
        cursor.execute('''
            CREATE TABLE ngos_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firebase_uid TEXT UNIQUE,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                registration_number TEXT NOT NULL,
                society_cert TEXT,
                trust_deed TEXT,
                section8_cert TEXT,
                verified INTEGER DEFAULT 0,
                auto_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Copy data (excluding password), keeping only unique emails
        cursor.execute('''
            INSERT INTO ngos_new (id, name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified)
            SELECT id, name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified
            FROM ngos
            WHERE id IN (
                SELECT MIN(id) FROM ngos GROUP BY email
            )
        ''')

        # Drop old table and rename new one
        cursor.execute("DROP TABLE ngos")
        cursor.execute("ALTER TABLE ngos_new RENAME TO ngos")

        cursor.execute("PRAGMA foreign_keys=on")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == '__main__':
    migrate_ngos_table()
