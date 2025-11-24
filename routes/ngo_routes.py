"""
NGO routes for food request management and volunteer rating
"""
from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from database.assignment_db import insert_ngo_assignment, insert_food_donor_request

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


# Additional route for NGO to review and accept food donor requests (moves data to food_donor_requests table first)
@ngo_bp.route('/review_accept_food_request', methods=['POST'])
def review_accept_food_request():
    """
    NGO reviews and initially accepts a food donor request.
    Moves from food_requests DB to food_donor_requests (pending review).
    Expects: ngo_id, request_id
    """
    try:
        data = request.get_json()
        ngo_id = data.get('ngo_id') or session.get('user_id')
        request_id = data.get('request_id')

        if not ngo_id or not request_id:
            return jsonify({'success': False, 'message': 'Missing ngo_id or request_id'}), 400
        
        conn_app = get_db_connection()
        conn_assign = get_assignment_db_connection()

        # Fetch the food request from food_requests table
        food_request = conn_app.execute('SELECT * FROM food_requests WHERE id = ?', (request_id,)).fetchone()
        if not food_request:
            conn_app.close()
            return jsonify({'success': False, 'message': 'Food request not found'}), 404
        
        # Insert into food_donor_requests in assignment.db with status 'pending'
        # Fetch NGO name
        ngo_row = conn_app.execute('SELECT name FROM ngos WHERE id = ?', (ngo_id,)).fetchone()
        ngo_name = ngo_row['name'] if ngo_row else 'Unknown NGO'

        # Insert into assignment db table with minimal data
        cursor = conn_assign.cursor()
        cursor.execute('''
            INSERT INTO food_donor_requests
            (assignment_id, food_donor_id, food_donor_name, ngo_id, ngo_name, status, ngo_acceptance_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (None, food_request['id'], food_request['donor_name'], ngo_id, ngo_name, 'pending', 'pending'))
        conn_assign.commit()

        # Optionally, delete from food_requests table as now transferred
        conn_app.execute('DELETE FROM food_requests WHERE id = ?', (request_id,))
        conn_app.commit()

        conn_app.close()
        conn_assign.close()

        return jsonify({'success': True, 'message': 'Food request moved to NGO pending acceptance.'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
