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

    # Food requests table (for donor donations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT,
            food_type TEXT NOT NULL,
            quantity TEXT NOT NULL,
            pickup_location TEXT NOT NULL,
            pickup_time TEXT,
            food_category TEXT,
            cuisine_type TEXT,
            spice_level TEXT,
            selected_ngo_id INTEGER,
            status TEXT DEFAULT 'requested',
            assigned_volunteer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (selected_ngo_id) REFERENCES ngos (id),
            FOREIGN KEY (assigned_volunteer_id) REFERENCES volunteers (id)
        )
    ''')

    # Food donors table (for registered food donors' donations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_name TEXT NOT NULL,
            food_type TEXT NOT NULL,
            quantity TEXT NOT NULL,
            ready_for_pickup_time TEXT,
            pickup_location TEXT NOT NULL,
            category TEXT,
            cuisine_type TEXT,
            spice_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    try:
        cursor.execute('ALTER TABLE volunteers ADD COLUMN average_rating REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE volunteers ADD COLUMN total_ratings INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Ensure selected_ngo_id column exists (for migration)
    try:
        cursor.execute('ALTER TABLE food_requests ADD COLUMN selected_ngo_id INTEGER REFERENCES ngos(id)')
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


def migrate_food_requests_to_food_donors():
    """Migrate data from food_requests to food_donors and drop food_requests table"""
    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()

    # Add missing columns to food_donors if they don't exist
    columns_to_add = [
        ('status', 'TEXT DEFAULT NULL'),
        ('assigned_volunteer_id', 'INTEGER'),
        ('pickup_lat', 'REAL'),
        ('pickup_lon', 'REAL'),
        ('selected_ngo_id', 'INTEGER')
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE food_donors ADD COLUMN {col_name} {col_type}')
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Insert data from food_requests into food_donors
    cursor.execute('''
        INSERT INTO food_donors (
            organization_name, food_type, quantity, ready_for_pickup_time,
            pickup_location, category, cuisine_type, spice_level,
            status, assigned_volunteer_id, pickup_lat, pickup_lon, selected_ngo_id, created_at
        )
        SELECT
            donor_name, food_type, quantity, pickup_time,
            pickup_location, food_category, cuisine_type, spice_level,
            status, assigned_volunteer_id, pickup_lat, pickup_lon, selected_ngo_id, created_at
        FROM food_requests
    ''')

    # Drop the food_requests table
    cursor.execute('DROP TABLE food_requests')

    conn.commit()
    conn.close()
    print("Migration completed: food_requests data merged into food_donors and table dropped.")


def create_auth_tables():
    """Create auth tables in auth.db"""
    conn = sqlite3.connect('database/auth.db')
    cursor = conn.cursor()

    # Users table for auth details
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firebase_uid TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            registration_number TEXT,
            primary_contact TEXT,
            society_cert TEXT,
            trust_deed TEXT,
            section8_cert TEXT,
            verified INTEGER DEFAULT 0,
            auto_verified INTEGER DEFAULT 0,
            current_session_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Sessions table to track active sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            user_type TEXT NOT NULL, -- 'NGO', 'Donor', 'Volunteer'
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Add session_id column to users if it doesn't exist
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN current_session_id TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


if __name__ == '__main__':
    create_tables()
    create_auth_tables()
    print("Tables created successfully.")
