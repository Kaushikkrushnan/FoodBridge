"""
SQLite database connection helper
"""
import sqlite3
import os

# Database paths
DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
AUTH_DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'auth.db')
VOLUNTEER_DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'volunteer.db')


def get_db_connection():
    """
    Create and return a SQLite database connection with Row factory.
    This allows accessing columns by name like a dictionary.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_auth_db_connection():
    """
    Create and return a SQLite database connection for auth.db with Row factory.
    """
    conn = sqlite3.connect(AUTH_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_volunteer_db_connection():
    """
    Create and return a SQLite database connection for volunteer.db with Row factory.
    """
    conn = sqlite3.connect(VOLUNTEER_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize the database with all required tables.
    """
    conn = get_db_connection()

    # NGOs table with updated schema
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ngos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            registration_number TEXT,
            society_cert TEXT,
            trust_deed TEXT,
            section8_cert TEXT,
            verified INTEGER DEFAULT 0,
            auto_verified INTEGER DEFAULT 0
        )
    ''')

    # Volunteers table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            lat REAL,
            lon REAL,
            available_from TEXT,
            available_to TEXT,
            is_available INTEGER DEFAULT 1,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Food requests table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS food_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT,
            food_type TEXT,
            quantity TEXT,
            pickup_location TEXT,
            pickup_lat REAL,
            pickup_lon REAL,
            pickup_time TEXT,
            status TEXT DEFAULT 'active',
            assigned_volunteer_id INTEGER,
            food_category TEXT,
            cuisine_type TEXT,
            spice_level TEXT
        )
    ''')

    conn.commit()
    conn.close()


def init_volunteer_db():
    """
    Initialize the volunteer database with volunteers table.
    """
    conn = get_volunteer_db_connection()

    # Volunteers table with updated schema
    conn.execute('''
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firebase_uid TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            availability TEXT,
            verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            average_rating REAL DEFAULT 0,
            total_ratings INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

