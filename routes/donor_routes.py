"""
Donor routes for food donation submission
"""
from flask import Blueprint, request, redirect, url_for
from db import get_db_connection

donor_bp = Blueprint('donor', __name__)


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
