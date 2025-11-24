"""
Session management for FoodBridge
Handles database-backed session storage and management
"""
import sqlite3
import secrets
import os
from datetime import datetime, timedelta
from db import get_auth_db_connection

# Session expiration time (24 hours)
SESSION_EXPIRY_HOURS = 24


def generate_session_id():
    """Generate a unique session ID"""
    return secrets.token_urlsafe(32)


def create_session(user_id, user_type, ip_address=None, user_agent=None):
    """
    Create a new session in the database
    
    Args:
        user_id: ID of the user
        user_type: Type of user ('NGO', 'Donor', 'Volunteer')
        ip_address: IP address of the client
        user_agent: User agent string
    
    Returns:
        session_id: The generated session ID
    """
    conn = get_auth_db_connection()
    cursor = conn.cursor()
    
    # Generate session ID
    session_id = generate_session_id()
    
    # Calculate expiration time
    expires_at = datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)
    
    # Deactivate any existing sessions for this user
    cursor.execute('''
        UPDATE sessions 
        SET is_active = 0 
        WHERE user_id = ? AND user_type = ? AND is_active = 1
    ''', (user_id, user_type))
    
    # Create new session
    cursor.execute('''
        INSERT INTO sessions (session_id, user_id, user_type, ip_address, user_agent, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, user_id, user_type, ip_address, user_agent, expires_at))
    
    # Update user's current_session_id
    cursor.execute('''
        UPDATE users 
        SET current_session_id = ? 
        WHERE id = ?
    ''', (session_id, user_id))
    
    conn.commit()
    conn.close()
    
    return session_id


def get_session(session_id):
    """
    Get session information from database
    
    Args:
        session_id: The session ID to look up
    
    Returns:
        dict: Session information or None if not found/invalid
    """
    conn = get_auth_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, u.name, u.email, u.registration_number, u.verified
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_id = ? AND s.is_active = 1
    ''', (session_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    # Check if session has expired
    expires_at = datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None
    if expires_at and datetime.now() > expires_at:
        # Session expired, deactivate it
        deactivate_session(session_id)
        return None
    
    return dict(row)


def update_session_activity(session_id):
    """Update last activity timestamp for a session"""
    conn = get_auth_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE sessions 
        SET last_activity = CURRENT_TIMESTAMP 
        WHERE session_id = ? AND is_active = 1
    ''', (session_id,))
    
    conn.commit()
    conn.close()


def deactivate_session(session_id):
    """
    Deactivate a session (logout)
    
    Args:
        session_id: The session ID to deactivate
    """
    conn = get_auth_db_connection()
    cursor = conn.cursor()
    
    # Get user_id before deactivating
    cursor.execute('SELECT user_id FROM sessions WHERE session_id = ?', (session_id,))
    row = cursor.fetchone()
    
    if row:
        user_id = row['user_id']
        # Deactivate session
        cursor.execute('''
            UPDATE sessions 
            SET is_active = 0 
            WHERE session_id = ?
        ''', (session_id,))
        
        # Clear user's current_session_id
        cursor.execute('''
            UPDATE users 
            SET current_session_id = NULL 
            WHERE id = ?
        ''', (user_id,))
    
    conn.commit()
    conn.close()


def deactivate_user_sessions(user_id, user_type):
    """
    Deactivate all active sessions for a user
    
    Args:
        user_id: ID of the user
        user_type: Type of user
    """
    conn = get_auth_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE sessions 
        SET is_active = 0 
        WHERE user_id = ? AND user_type = ? AND is_active = 1
    ''', (user_id, user_type))
    
    cursor.execute('''
        UPDATE users 
        SET current_session_id = NULL 
        WHERE id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()


def cleanup_expired_sessions():
    """Remove expired sessions from database"""
    conn = get_auth_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE sessions 
        SET is_active = 0 
        WHERE expires_at < CURRENT_TIMESTAMP AND is_active = 1
    ''')
    
    conn.commit()
    conn.close()


def get_user_from_session(session_id):
    """
    Get user information from session ID
    
    Args:
        session_id: The session ID
    
    Returns:
        dict: User information or None
    """
    session = get_session(session_id)
    if not session:
        return None
    
    return {
        'user_id': session['user_id'],
        'user_name': session['name'],
        'user_email': session['email'],
        'user_role': session['user_type'],
        'user_registration': session.get('registration_number', ''),
        'user_verified': bool(session.get('verified', 0))
    }

