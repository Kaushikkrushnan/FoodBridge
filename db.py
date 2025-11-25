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
            auto_verified INTEGER DEFAULT 0,
            address TEXT,
            lat REAL,
            lon REAL
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
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            average_rating REAL DEFAULT 0,
            total_ratings INTEGER DEFAULT 0
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
            spice_level TEXT,
            ngo_id INTEGER,
            completed_at TIMESTAMP
        )
    ''')

    # Food donors table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS food_donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            whatsapp_phone TEXT,
            vehicle_type TEXT,
            address TEXT,
            food_type TEXT,
            quantity TEXT,
            ready_for_pickup_time TEXT,
            pickup_location TEXT,
            category TEXT,
            cuisine_type TEXT,
            spice_level TEXT,
            status TEXT DEFAULT 'pending',
            selected_ngo_id INTEGER,
            assigned_volunteer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Complaints table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_type TEXT,
            reporter_id INTEGER,
            complaint_type TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            admin_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')

    # Volunteer ratings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS volunteer_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngo_id INTEGER,
            volunteer_id INTEGER,
            rating INTEGER,
            review TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def init_auth_db():
    """
    Initialize the auth database with users and sessions tables.
    """
    conn = get_auth_db_connection()

    # Users table for NGO authentication
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firebase_uid TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            registration_number TEXT,
            society_cert TEXT,
            trust_deed TEXT,
            section8_cert TEXT,
            verified INTEGER DEFAULT 0,
            auto_verified INTEGER DEFAULT 0,
            current_session_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Sessions table for session management
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            user_type TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
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


def init_all_databases():
    """
    Initialize all databases with required tables.
    """
    init_db()
    init_auth_db()
    init_volunteer_db()
    
    # Also initialize assignment database
    from database.assignment_db import create_assignment_tables
    create_assignment_tables()

