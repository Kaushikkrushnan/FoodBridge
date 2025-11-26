"""
Mock Authentication Module for FoodBridge
When USE_MOCK_AUTH = True, Firebase authentication is bypassed and local DB auth is used.
This allows testing without external Firebase dependencies.

To switch back to Firebase auth, set USE_MOCK_AUTH = False
"""
import sqlite3
import hashlib
import os

# Configuration flag: Set to True to use mock auth, False for real Firebase
USE_MOCK_AUTH = True

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    return stored_hash == hash_password(password)

def mock_authenticate(email, password, role):
    """
    Mock authentication function for local DB authentication.
    Returns user data dict if authenticated, None otherwise.
    
    Args:
        email: User email
        password: User password (plaintext)
        role: One of 'donor', 'ngo', 'volunteer'
    
    Returns:
        dict: User data if authenticated
        None: If authentication fails
    """
    from db import get_db_connection, get_volunteer_db_connection
    
    if role == 'donor':
        conn = get_db_connection()
        user = conn.execute('''
            SELECT id, organization_name as name, email, phone, password_hash
            FROM food_donors WHERE email = ?
        ''', (email,)).fetchone()
        conn.close()
        
        if user and user['password_hash']:
            if verify_password(user['password_hash'], password):
                return {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'role': 'donor'
                }
        return None
        
    elif role == 'ngo':
        conn = get_db_connection()
        user = conn.execute('''
            SELECT id, name, email, registration_number, password_hash, verified
            FROM ngos WHERE email = ?
        ''', (email,)).fetchone()
        conn.close()
        
        if user and user['password_hash']:
            if verify_password(user['password_hash'], password):
                return {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'registration_number': user['registration_number'],
                    'verified': bool(user['verified']),
                    'role': 'ngo'
                }
        return None
        
    elif role == 'volunteer':
        conn = get_volunteer_db_connection()
        user = conn.execute('''
            SELECT id, name, email, phone, password_hash, verified
            FROM volunteers WHERE email = ?
        ''', (email,)).fetchone()
        conn.close()
        
        if user and user['password_hash']:
            if verify_password(user['password_hash'], password):
                return {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'phone': user['phone'],
                    'verified': bool(user['verified']),
                    'role': 'volunteer'
                }
        return None
    
    return None

def mock_register(user_data, role):
    """
    Mock registration function for local DB registration.
    
    Args:
        user_data: dict with user registration data
        role: One of 'donor', 'ngo', 'volunteer'
    
    Returns:
        dict: {'success': True, 'user_id': id} if successful
        dict: {'success': False, 'message': error} if failed
    """
    from db import get_db_connection, get_volunteer_db_connection
    
    password_hash = hash_password(user_data.get('password', ''))
    
    try:
        if role == 'donor':
            conn = get_db_connection()
            # Check if email already exists
            existing = conn.execute('SELECT id FROM food_donors WHERE email = ?', 
                                   (user_data.get('email'),)).fetchone()
            if existing:
                conn.close()
                return {'success': False, 'message': 'Email already registered'}
            
            cursor = conn.execute('''
                INSERT INTO food_donors (organization_name, email, phone, whatsapp_phone, 
                                        vehicle_type, address, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_data.get('name'), user_data.get('email'), user_data.get('phone'),
                  user_data.get('whatsapp_phone'), user_data.get('vehicle_type'),
                  user_data.get('address'), password_hash))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {'success': True, 'user_id': user_id}
            
        elif role == 'ngo':
            conn = get_db_connection()
            # Check if email already exists
            existing = conn.execute('SELECT id FROM ngos WHERE email = ?', 
                                   (user_data.get('email'),)).fetchone()
            if existing:
                conn.close()
                return {'success': False, 'message': 'Email already registered'}
            
            cursor = conn.execute('''
                INSERT INTO ngos (name, email, registration_number, password_hash, 
                                 primary_contact, verified, auto_verified)
                VALUES (?, ?, ?, ?, ?, 0, 0)
            ''', (user_data.get('name'), user_data.get('email'), 
                  user_data.get('registration_number'), password_hash,
                  user_data.get('primary_contact', '')))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {'success': True, 'user_id': user_id}
            
        elif role == 'volunteer':
            conn = get_volunteer_db_connection()
            # Check if email already exists
            existing = conn.execute('SELECT id FROM volunteers WHERE email = ?', 
                                   (user_data.get('email'),)).fetchone()
            if existing:
                conn.close()
                return {'success': False, 'message': 'Email already registered'}
            
            cursor = conn.execute('''
                INSERT INTO volunteers (name, email, phone, password_hash, 
                                       verified, created_at, average_rating, total_ratings)
                VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, 0, 0)
            ''', (user_data.get('name'), user_data.get('email'), 
                  user_data.get('phone'), password_hash))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {'success': True, 'user_id': user_id}
    
    except Exception as e:
        return {'success': False, 'message': str(e)}
    
    return {'success': False, 'message': 'Unknown role'}
