"""
NGO routes for food request management and volunteer rating
"""
from flask import Blueprint, request, jsonify
from db import get_db_connection

ngo_bp = Blueprint('ngo', __name__)


@ngo_bp.route('/submit_food_request', methods=['POST'])
def submit_food_request():
    """
    Handle NGO food request submission.
    Expects: ngo_id, food_type, quantity, urgency, location, contact_person, contact_phone
    """
    try:
        data = request.get_json()

        ngo_id = data.get('ngo_id')
        food_type = data.get('food_type')
        quantity = data.get('quantity')
        urgency = data.get('urgency')
        location = data.get('location')
        contact_person = data.get('contact_person')
        contact_phone = data.get('contact_phone')

        if not all([ngo_id, food_type, quantity, urgency, location]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO food_requests (ngo_id, food_type, quantity, urgency, location, contact_person, contact_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ngo_id, food_type, quantity, urgency, location, contact_person, contact_phone))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Food request submitted successfully'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@ngo_bp.route('/rate_volunteer', methods=['POST'])
def rate_volunteer():
    """
    Allow NGO to rate a volunteer after delivery completion.
    Expects: ngo_id, volunteer_id, rating (1-5), review (optional)
    """
    try:
        data = request.get_json()

        ngo_id = data.get('ngo_id')
        volunteer_id = data.get('volunteer_id')
        rating = data.get('rating')
        review = data.get('review', '')

        if not all([ngo_id, volunteer_id, rating]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        if not (1 <= rating <= 5):
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400

        conn = get_db_connection()

        # Insert rating
        conn.execute('''
            INSERT INTO volunteer_ratings (ngo_id, volunteer_id, rating, review)
            VALUES (?, ?, ?, ?)
        ''', (ngo_id, volunteer_id, rating, review))

        # Update volunteer's average rating
        conn.execute('''
            UPDATE volunteers
            SET average_rating = (
                SELECT AVG(rating) FROM volunteer_ratings WHERE volunteer_id = ?
            ),
            total_ratings = (
                SELECT COUNT(*) FROM volunteer_ratings WHERE volunteer_id = ?
            )
            WHERE id = ?
        ''', (volunteer_id, volunteer_id, volunteer_id))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Volunteer rated successfully'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@ngo_bp.route('/get_volunteer_ratings/<volunteer_id>', methods=['GET'])
def get_volunteer_ratings(volunteer_id):
    """
    Get all ratings for a specific volunteer.
    """
    try:
        conn = get_db_connection()
        ratings = conn.execute('''
            SELECT vr.rating, vr.review, vr.created_at, n.name as ngo_name
            FROM volunteer_ratings vr
            JOIN ngos n ON vr.ngo_id = n.id
            WHERE vr.volunteer_id = ?
            ORDER BY vr.created_at DESC
        ''', (volunteer_id,)).fetchall()
        conn.close()

        ratings_list = [dict(row) for row in ratings]

        return jsonify({
            'success': True,
            'ratings': ratings_list
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@ngo_bp.route('/accept_food_request', methods=['POST'])
def accept_food_request():
    """
    NGO accepts a food donation request, assigns nearest volunteer.
    Expects: ngo_id, request_id
    """
    try:
        data = request.get_json()
        ngo_id = data.get('ngo_id')
        request_id = data.get('request_id')

        if not ngo_id or not request_id:
            return jsonify({'success': False, 'message': 'Missing ngo_id or request_id'}), 400

        conn = get_db_connection()

        # Get request details including pickup location
        request_data = conn.execute('''
            SELECT pickup_lat, pickup_lon, ngo_id as current_ngo_id
            FROM food_requests WHERE id = ?
        ''', (request_id,)).fetchone()

        if not request_data:
            conn.close()
            return jsonify({'success': False, 'message': 'Request not found'}), 404

        if request_data['current_ngo_id']:
            conn.close()
            return jsonify({'success': False, 'message': 'Request already accepted by another NGO'}), 400

        pickup_lat = request_data['pickup_lat']
        pickup_lon = request_data['pickup_lon']

        if not pickup_lat or not pickup_lon:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid pickup location'}), 400

        # Find nearest volunteer using distance and rating (70% distance, 30% rating)
        volunteers = conn.execute('''
            SELECT id, name, lat, lon, average_rating,
                   (6371 * acos(cos(radians(?)) * cos(radians(lat)) * cos(radians(lon) - radians(?)) + sin(radians(?)) * sin(radians(lat)))) AS distance
            FROM volunteers
            WHERE verified = 1
            ORDER BY (0.7 * distance + 0.3 * (5 - COALESCE(average_rating, 0))) ASC
            LIMIT 1
        ''', (pickup_lat, pickup_lon, pickup_lat)).fetchone()

        if not volunteers:
            conn.close()
            return jsonify({'success': False, 'message': 'No available volunteers'}), 400

        volunteer_id = volunteers['id']
        volunteer_name = volunteers['name']

        # Update request: set ngo_id, status='assigned', assigned_volunteer_id
        conn.execute('''
            UPDATE food_requests
            SET ngo_id = ?, status = 'assigned', assigned_volunteer_id = ?
            WHERE id = ?
        ''', (ngo_id, volunteer_id, request_id))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Request accepted! {volunteer_name} assigned.',
            'volunteer_name': volunteer_name
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
