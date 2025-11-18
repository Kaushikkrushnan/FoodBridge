"""
Donor routes for food donation submission
"""
from flask import Blueprint, request, redirect, url_for
from db import get_db_connection

donor_bp = Blueprint('donor', __name__)


@donor_bp.route('/submit_food_request', methods=['POST'])
def submit_food_request():
    """
    Handle food donation submission and redirect to donor dashboard.
    """
    # Get form data
    donor_name = request.form.get('donor_name')
    food_type = request.form.get('food_type')
    quantity = request.form.get('quantity')
    pickup_location = request.form.get('pickup_location')
    pickup_time = request.form.get('pickup_time')
    food_category = request.form.get('food_category')
    cuisine_type = request.form.get('cuisine_type')
    spice_level = request.form.get('spice_level')

    # Insert into database
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO food_requests (donor_name, food_type, quantity, pickup_location, pickup_time, food_category, cuisine_type, spice_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (donor_name, food_type, quantity, pickup_location, pickup_time, food_category, cuisine_type, spice_level))
    conn.commit()
    conn.close()

    # Redirect to homepage to show live tracking
    return redirect(url_for('index'))
