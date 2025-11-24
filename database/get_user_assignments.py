import sqlite3
import os

ASSIGNMENT_DB_PATH = os.path.join(os.path.dirname(__file__), 'assignment.db')

def get_user_assignments(user_email):
    conn = sqlite3.connect(ASSIGNMENT_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Find assignments where the user is a food donor, volunteer, or NGO
    cursor.execute('''
        SELECT * FROM ngo_assignments
        WHERE food_donor_name = ? OR volunteer_name = ? OR ngo_name = ?
        ORDER BY assigned_at DESC
    ''', (user_email, user_email, user_email))
    assignments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return assignments
