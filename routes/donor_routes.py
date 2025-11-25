"""
Donor routes for food donation submission
"""
from flask import Blueprint, request, redirect, url_for, session, jsonify
from db import get_db_connection

donor_bp = Blueprint('donor', __name__)
@donor_bp.route('/accept_ngo', methods=['POST'])
def accept_ngo():
    """
    Donor accepts an NGO for their donation. Updates assignment and request status to 'accepted'.
    Expects JSON: { 'ngo_id': ..., 'ngo_name': ... }
    """
    data = request.get_json()
    ngo_id = data.get('ngo_id')
    ngo_name = data.get('ngo_name')
    donor_name = session.get('user_name')
    donor_id = None
    # Get donor_id from food_donors table
    conn = get_db_connection()
    donor_row = conn.execute('SELECT id FROM food_donors WHERE organization_name = ?', (donor_name,)).fetchone()
    if donor_row:
        donor_id = donor_row['id']
    conn.close()
    if not donor_id or not ngo_id:
        return jsonify({'success': False, 'error': 'Missing donor or NGO info'}), 400
    # Insert assignment and request, set status to accepted
    from database.assignment_db import insert_ngo_assignment, insert_food_donor_request
    assignment_id = insert_ngo_assignment(
        ngo_id=int(ngo_id),
        ngo_name=ngo_name,
        volunteer_id=None,
        volunteer_name=None,
        food_donor_id=donor_id,
        food_donor_name=donor_name,
        session_key=session.get('user_session_key', '')
    )
    insert_food_donor_request(
        assignment_id=assignment_id,
        food_donor_id=donor_id,
        food_donor_name=donor_name,
        ngo_id=int(ngo_id),
        ngo_name=ngo_name
    )
    # Update status to accepted
    from database.assignment_db import update_ngo_acceptance_status
    # Get request_id
    import sqlite3
    conn = sqlite3.connect('database/assignment.db')
    conn.row_factory = sqlite3.Row
    req_row = conn.execute('SELECT id FROM food_donor_requests WHERE assignment_id = ? AND ngo_id = ?', (assignment_id, ngo_id)).fetchone()
    if req_row:
        update_ngo_acceptance_status(req_row['id'], 'accepted')
    conn.close()
    print(f"DEBUG: Donor {donor_name} (id={donor_id}) accepted NGO {ngo_name} (id={ngo_id}), assignment_id={assignment_id}")
    return jsonify({'success': True, 'assignment_id': assignment_id})

@donor_bp.route('/submit_food_request', methods=['POST'])
def submit_food_request():
    """
    Handle food donation submission for registered donors and redirect to donor dashboard.
    """
    # Get form data
    organization_name = request.form.get('donor_name')
    phone = request.form.get('phone')
    food_type = request.form.get('food_type')
    quantity = request.form.get('quantity')
    ready_for_pickup_time = request.form.get('pickup_time')
    pickup_location = request.form.get('pickup_location')
    category = request.form.get('food_category')
    cuisine_type = request.form.get('cuisine_type')
    spice_level = request.form.get('spice_level')

    # Insert into food_donors table
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO food_donors (organization_name, phone, food_type, quantity, ready_for_pickup_time, pickup_location, category, cuisine_type, spice_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (organization_name, phone, food_type, quantity, ready_for_pickup_time, pickup_location, category, cuisine_type, spice_level))
    conn.commit()
    conn.close()

    # Redirect to donor dashboard
    return redirect(url_for('dashboard.donor_dashboard'))
