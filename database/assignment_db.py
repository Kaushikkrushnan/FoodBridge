import sqlite3
import os

ASSIGNMENT_DB_PATH = os.path.join(os.path.dirname(__file__), 'assignment.db')

def get_assignment_db_connection():
    conn = sqlite3.connect(ASSIGNMENT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_assignment_tables():
    conn = get_assignment_db_connection()
    cursor = conn.cursor()

    # Table to store assignments: volunteers assigned, food donors accepted by NGOs, and NGOs details with session keys
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ngo_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ngo_id INTEGER NOT NULL,
        ngo_name TEXT,
        volunteer_id INTEGER,
        volunteer_name TEXT,
        food_donor_id INTEGER,
        food_donor_name TEXT,
        session_key TEXT,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        request_status TEXT DEFAULT 'requested', -- 'requested', 'accepted', 'rejected'
        acceptance_time TIMESTAMP,
        volunteer_allocated_time TIMESTAMP
    )
    """)

    # Table to store requested food donors and NGOs who requested them, linked to ngo_assignments by assignment_id
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_donor_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assignment_id INTEGER NOT NULL,
        food_donor_id INTEGER NOT NULL,
        food_donor_name TEXT,
        ngo_id INTEGER NOT NULL,
        ngo_name TEXT,
        request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',  -- 'pending', 'accepted', 'rejected'
        ngo_acceptance_status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'rejected'
        volunteer_id INTEGER,
        volunteer_name TEXT,
        volunteer_allocated_time TIMESTAMP,
        FOREIGN KEY (assignment_id) REFERENCES ngo_assignments(id)
    )
    """)

def request_food_donation(food_donor_id, food_donor_name, ngo_id, ngo_name):
    conn = get_assignment_db_connection()
    cursor = conn.cursor()
    # Create assignment with status 'requested'
    cursor.execute("""
        INSERT INTO ngo_assignments (ngo_id, ngo_name, food_donor_id, food_donor_name, request_status)
        VALUES (?, ?, ?, ?, 'requested')
    """, (ngo_id, ngo_name, food_donor_id, food_donor_name))
    assignment_id = cursor.lastrowid
    # Add to food_donor_requests
    cursor.execute("""
        INSERT INTO food_donor_requests (assignment_id, food_donor_id, food_donor_name, ngo_id, ngo_name, status, ngo_acceptance_status)
        VALUES (?, ?, ?, ?, ?, 'pending', 'pending')
    """, (assignment_id, food_donor_id, food_donor_name, ngo_id, ngo_name))
    conn.commit()
    conn.close()
    return assignment_id

def accept_food_donation_request(request_id, volunteer_id=None, volunteer_name=None):
    conn = get_assignment_db_connection()
    cursor = conn.cursor()
    # Update request status to accepted
    cursor.execute("""
        UPDATE food_donor_requests
        SET status = 'accepted', ngo_acceptance_status = 'accepted', volunteer_id = ?, volunteer_name = ?, volunteer_allocated_time = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (volunteer_id, volunteer_name, request_id))
    # Also update assignment
    cursor.execute("""
        UPDATE ngo_assignments
        SET request_status = 'accepted', acceptance_time = CURRENT_TIMESTAMP, volunteer_id = ?, volunteer_name = ?, volunteer_allocated_time = CURRENT_TIMESTAMP
        WHERE id = (SELECT assignment_id FROM food_donor_requests WHERE id = ?)
    """, (volunteer_id, volunteer_name, request_id))
    conn.commit()
    conn.close()

    conn.commit()
    conn.close()

def insert_ngo_assignment(ngo_id, ngo_name, volunteer_id, volunteer_name, food_donor_id, food_donor_name, session_key):
    conn = get_assignment_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ngo_assignments
        (ngo_id, ngo_name, volunteer_id, volunteer_name, food_donor_id, food_donor_name, session_key)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ngo_id, ngo_name, volunteer_id, volunteer_name, food_donor_id, food_donor_name, session_key))

    conn.commit()
    assignment_id = cursor.lastrowid
    conn.close()
    return assignment_id

def update_ngo_acceptance_status(request_id, status):
    """
    Update ngo_acceptance_status for a food donor request.
    Status can be 'pending', 'accepted', or 'rejected'.
    """
    conn = get_assignment_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE food_donor_requests
        SET ngo_acceptance_status = ?
        WHERE id = ?
    """, (status, request_id))

    conn.commit()
    conn.close()


def insert_food_donor_request(assignment_id, food_donor_id, food_donor_name, ngo_id, ngo_name):
    conn = get_assignment_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO food_donor_requests
        (assignment_id, food_donor_id, food_donor_name, ngo_id, ngo_name, ngo_acceptance_status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    """, (assignment_id, food_donor_id, food_donor_name, ngo_id, ngo_name))

    conn.commit()
    conn.close()

# Example usage:
if __name__ == "__main__":
    create_assignment_tables()
    assignment_id = insert_ngo_assignment(1, "Helping Hands NGO", 3, "John Doe", 5, "Food Donor Inc.", "sess123456")
    insert_food_donor_request(assignment_id, 5, "Food Donor Inc.", 1, "Helping Hands NGO")
    print("Assignment and food donor requests inserted.")
