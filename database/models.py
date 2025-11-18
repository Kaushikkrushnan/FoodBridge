# Database models and schema for FoodBridge

import sqlite3

def create_tables():
    """Create all necessary tables if they don't exist"""
    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()

    # NGOs table with Firebase UID instead of password
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ngos (
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
            lat REAL,
            lon REAL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Volunteers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firebase_uid TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            skills TEXT,
            availability TEXT,
            verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Food requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngo_id INTEGER,
            food_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            urgency TEXT NOT NULL,
            location TEXT NOT NULL,
            pickup_lat REAL,
            pickup_lon REAL,
            contact_person TEXT,
            contact_phone TEXT,
            status TEXT DEFAULT 'pending',
            assigned_volunteer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ngo_id) REFERENCES ngos (id),
            FOREIGN KEY (assigned_volunteer_id) REFERENCES volunteers (id)
        )
    ''')

    # Volunteer ratings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteer_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngo_id INTEGER,
            volunteer_id INTEGER,
            rating INTEGER NOT NULL,
            review TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ngo_id) REFERENCES ngos (id),
            FOREIGN KEY (volunteer_id) REFERENCES volunteers (id)
        )
    ''')

    # Complaints/issues table for admin management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_type TEXT NOT NULL, -- 'ngo', 'volunteer', 'donor'
            reporter_id INTEGER NOT NULL,
            complaint_type TEXT NOT NULL, -- 'volunteer_issue', 'ngo_issue', 'system_issue', etc.
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending', -- 'pending', 'investigating', 'resolved'
            admin_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Update volunteers table to include rating fields
    cursor.execute('ALTER TABLE volunteers ADD COLUMN average_rating REAL DEFAULT 0')
    cursor.execute('ALTER TABLE volunteers ADD COLUMN total_ratings INTEGER DEFAULT 0')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    print("Tables created successfully.")
