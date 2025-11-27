"""
Migration script to add location fields (lat, lng, location_text) to required tables.
This script safely adds columns if they don't exist.
"""
import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
AUTH_DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'auth.db')


def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_column_if_not_exists(conn, table_name, column_name, column_type):
    """Add a column to a table if it doesn't already exist."""
    if not column_exists(conn, table_name, column_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        print(f"Added column '{column_name}' to table '{table_name}'")
    else:
        print(f"Column '{column_name}' already exists in table '{table_name}'")


def migrate_app_db():
    """Add location fields to app.db tables."""
    conn = sqlite3.connect(DATABASE)
    
    # Add location fields to food_donors table
    add_column_if_not_exists(conn, 'food_donors', 'lat', 'REAL')
    add_column_if_not_exists(conn, 'food_donors', 'lng', 'REAL')
    add_column_if_not_exists(conn, 'food_donors', 'location_text', 'TEXT')
    
    # Add location fields to ngos table (lat already exists as lat, add lng and location_text)
    add_column_if_not_exists(conn, 'ngos', 'lng', 'REAL')
    add_column_if_not_exists(conn, 'ngos', 'location_text', 'TEXT')
    
    conn.commit()
    conn.close()
    print("app.db migration completed successfully!")


def migrate_auth_db():
    """Add location fields to auth.db users table."""
    conn = sqlite3.connect(AUTH_DATABASE)
    
    # Add location fields to users table
    add_column_if_not_exists(conn, 'users', 'lat', 'REAL')
    add_column_if_not_exists(conn, 'users', 'lng', 'REAL')
    add_column_if_not_exists(conn, 'users', 'location_text', 'TEXT')
    
    conn.commit()
    conn.close()
    print("auth.db migration completed successfully!")


if __name__ == "__main__":
    print("Starting location fields migration...")
    migrate_app_db()
    migrate_auth_db()
    print("All migrations completed!")
