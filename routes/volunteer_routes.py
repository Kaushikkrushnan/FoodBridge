"""
Volunteer management routes
Includes registration, location updates, and assignment logic
"""
from flask import Blueprint, request, jsonify
from db import get_db_connection
import math
from datetime import datetime

volunteer_bp = Blueprint('volunteer', __name__)


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


def time_in_slot(check_time, available_from, available_to):
    """
    Check if a given time falls within volunteer's availability slot.
    Times are in HH:MM format (24-hour).
    Returns True if time is within slot, False otherwise.
    """
    try:
        check = datetime.strptime(check_time, '%H:%M').time()
        from_time = datetime.strptime(available_from, '%H:%M').time()
        to_time = datetime.strptime(available_to, '%H:%M').time()
        
        return from_time <= check <= to_time
    except:
        return False


@volunteer_bp.route('/register_volunteer', methods=['POST'])
def register_volunteer():
    """
    Register a new volunteer with location and availability.
    Expects: name, contact, lat, lon, available_from, available_to
    """
    try:
        data = request.get_json()
        
        name = data.get('name')
        contact = data.get('contact')
        lat = data.get('lat')
        lon = data.get('lon')
        available_from = data.get('available_from')  # Format: 'HH:MM'
        available_to = data.get('available_to')  # Format: 'HH:MM'
        
        if not name or not contact:
            return jsonify({'success': False, 'message': 'Name and contact required'}), 400
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO volunteers (name, contact, lat, lon, available_from, available_to, is_available, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (name, contact, lat, lon, available_from, available_to))
        conn.commit()
        volunteer_id = conn.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Volunteer registered successfully',
            'volunteer_id': volunteer_id
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@volunteer_bp.route('/update_volunteer_location', methods=['POST'])
def update_volunteer_location():
    """
    Update volunteer's location, availability, and last_seen timestamp.
    Expects: volunteer_id, lat, lon, is_available (optional)
    """
    try:
        data = request.get_json()
        
        volunteer_id = data.get('volunteer_id')
        lat = data.get('lat')
        lon = data.get('lon')
        is_available = data.get('is_available', 1)
        
        if not volunteer_id:
            return jsonify({'success': False, 'message': 'Volunteer ID required'}), 400
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE volunteers
            SET lat = ?, lon = ?, is_available = ?, last_seen = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (lat, lon, is_available, volunteer_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Location updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@volunteer_bp.route('/get_available_volunteers', methods=['GET'])
def get_available_volunteers():
    """
    Get available volunteers sorted by distance from pickup location.
    Query params: pickup_lat, pickup_lon, pickup_time (HH:MM format)
    """
    try:
        pickup_lat = float(request.args.get('pickup_lat', 0))
        pickup_lon = float(request.args.get('pickup_lon', 0))
        pickup_time = request.args.get('pickup_time', '12:00')
        
        conn = get_db_connection()
        # Get all available volunteers
        volunteers = conn.execute('''
            SELECT * FROM volunteers WHERE is_available = 1
        ''').fetchall()
        conn.close()
        
        # Calculate distances and filter by time slot
        volunteer_list = []
        for vol in volunteers:
            if vol['lat'] and vol['lon']:
                distance = haversine(pickup_lat, pickup_lon, vol['lat'], vol['lon'])
                
                # Check if volunteer is available at pickup time
                available = True
                if vol['available_from'] and vol['available_to']:
                    available = time_in_slot(pickup_time, vol['available_from'], vol['available_to'])
                
                if available:
                    volunteer_list.append({
                        'id': vol['id'],
                        'name': vol['name'],
                        'contact': vol['contact'],
                        'distance': round(distance, 2),
                        'lat': vol['lat'],
                        'lon': vol['lon']
                    })
        
        # Sort by distance
        volunteer_list.sort(key=lambda x: x['distance'])
        
        return jsonify({
            'success': True,
            'volunteers': volunteer_list
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@volunteer_bp.route('/assign_nearest_volunteer', methods=['POST'])
def assign_nearest_volunteer():
    """
    Find and assign the nearest available volunteer to a food request.
    Uses ranking algorithm considering distance and volunteer rating.
    Expects: request_id (coordinates are read from database)
    """
    try:
        data = request.get_json()

        request_id = data.get('request_id')

        if not request_id:
            return jsonify({'success': False, 'message': 'Request ID required'}), 400

        # Get food request details from database
        conn = get_db_connection()
        food_request = conn.execute('''
            SELECT * FROM food_requests WHERE id = ?
        ''', (request_id,)).fetchone()

        if not food_request:
            conn.close()
            return jsonify({'success': False, 'message': 'Food request not found'}), 404

        pickup_lat = food_request['pickup_lat']
        pickup_lon = food_request['pickup_lon']
        pickup_time = food_request['pickup_time']

        if not pickup_lat or not pickup_lon:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid pickup location coordinates'}), 400

        # Get available volunteers with ratings
        volunteers = conn.execute('''
            SELECT *, COALESCE(average_rating, 0) as avg_rating, COALESCE(total_ratings, 0) as rating_count
            FROM volunteers WHERE is_available = 1
        ''').fetchall()

        # Find best volunteer using ranking algorithm
        best_volunteer = None
        best_score = float('-inf')

        for vol in volunteers:
            if vol['lat'] and vol['lon']:
                distance = haversine(pickup_lat, pickup_lon, vol['lat'], vol['lon'])

                # Check availability at pickup time
                available = True
                if vol['available_from'] and vol['available_to'] and pickup_time:
                    available = time_in_slot(pickup_time, vol['available_from'], vol['available_to'])

                if available:
                    # Ranking algorithm: prioritize distance (70%) and rating (30%)
                    # Lower distance is better, higher rating is better
                    distance_score = max(0, 10 - distance)  # Max score for distances under 10km
                    rating_score = vol['avg_rating'] if vol['avg_rating'] > 0 else 2.5  # Default rating of 2.5

                    # Weighted score
                    total_score = (distance_score * 0.7) + (rating_score * 0.3)

                    if total_score > best_score:
                        best_score = total_score
                        best_volunteer = vol

        if not best_volunteer:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'No available volunteers found'
            }), 404

        # Update food request with assigned volunteer
        conn.execute('''
            UPDATE food_requests
            SET assigned_volunteer_id = ?, status = 'assigned'
            WHERE id = ?
        ''', (best_volunteer['id'], request_id))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'status': 'assigned',
            'message': 'Volunteer assigned successfully',
            'volunteer': {
                'id': best_volunteer['id'],
                'name': best_volunteer['name'],
                'contact': best_volunteer['contact'],
                'rating': round(best_volunteer['avg_rating'], 1),
                'total_ratings': best_volunteer['rating_count']
            },
            'volunteer_name': best_volunteer['name'],
            'distance': round(haversine(pickup_lat, pickup_lon, best_volunteer['lat'], best_volunteer['lon']), 2),
            'distance_km': round(haversine(pickup_lat, pickup_lon, best_volunteer['lat'], best_volunteer['lon']), 2)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

