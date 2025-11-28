"""
Dashboard routes for Donor and NGO dashboards
"""
from flask import Blueprint, render_template, session, request, jsonify
from db import get_db_connection, get_auth_db_connection
from database.session_manager import get_user_from_session, update_session_activity

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/accept_ngo', methods=['POST'])
def accept_ngo():
    """
    Backend route for donor accepting an NGO. Assigns NGO to donor and creates assignment record.
    """
    data = request.get_json()
    print('[DEBUG] /accept_ngo incoming data:', data)
    ngo_id = data.get('ngo_id')
    ngo_name = data.get('ngo_name')
    # Get donor info from session
    print('[DEBUG] Session in /accept_ngo:', dict(session))
    
    # Try to get donor info from session first
    donor_name = session.get('user_name')
    donor_id = session.get('user_id')
    
    # If session doesn't have donor info, try to get from database session
    if not donor_name or not donor_id:
        db_session_id = session.get('db_session_id')
        if db_session_id:
            db_user = get_user_from_session(db_session_id)
            if db_user:
                donor_name = db_user.get('user_name')
                donor_id = db_user.get('user_id')
                update_session_activity(db_session_id)
    
    # If still no donor info, try to get from user_contact (for food donors logged in via phone)
    if not donor_name or not donor_id:
        user_contact = session.get('user_contact')
        if user_contact:
            try:
                conn = get_db_connection()
                donor_record = conn.execute(
                    'SELECT id, organization_name FROM food_donors WHERE phone = ? OR email = ?',
                    (user_contact, user_contact)
                ).fetchone()
                conn.close()
                if donor_record:
                    donor_id = donor_record['id']
                    donor_name = donor_record['organization_name']
                    # Update session with the found values
                    session['user_id'] = donor_id
                    session['user_name'] = donor_name
            except Exception as e:
                print(f'[DEBUG] Error fetching donor from contact: {e}')
    
    missing = []
    if not ngo_id:
        missing.append('ngo_id')
    if not ngo_name:
        missing.append('ngo_name')
    if not donor_name:
        missing.append('donor_name (Please login as a food donor first)')
    if not donor_id:
        missing.append('donor_id (Please login as a food donor first)')
    if missing:
        return jsonify({'success': False, 'error': f'Missing required fields: {", ".join(missing)}'}), 400
    try:
        # Insert assignment into assignment_db
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        # Insert new assignment record
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ngo_assignments (food_donor_id, food_donor_name, ngo_id, ngo_name, assigned_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (donor_id, donor_name, ngo_id, ngo_name))
        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f'[DEBUG] Assignment created: donor_id={donor_id}, ngo_id={ngo_id}, assignment_id={assignment_id}')
        return jsonify({'success': True, 'assignment_id': assignment_id})
    except Exception as e:
        import traceback
        print('[ERROR] Exception in /accept_ngo:')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
@dashboard_bp.route('/ngo_accept_donation', methods=['POST'])
def ngo_accept_donation():
    data = request.get_json()
    print('[DEBUG] /ngo_accept_donation incoming data:', data)
    request_id = data.get('request_id')
    if not request_id:
        return jsonify({'success': False, 'error': 'Missing request_id'}), 400
    import traceback
    try:
        # Get current NGO info from session
        ngo_id = session.get('user_id')
        ngo_name = session.get('user_name')
        
        # Update the food_donors table to mark this donation as accepted
        conn = get_db_connection()
        conn.execute('''
            UPDATE food_donors 
            SET status = 'accepted', selected_ngo_id = ?
            WHERE id = ?
        ''', (ngo_id, request_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print('[ERROR] Exception in ngo_accept_donation:')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/donor_dashboard')
def donor_dashboard():
    from flask import session
    print('[DEBUG] Session at donor_dashboard:', dict(session))
    """
    Render donor dashboard showing Available NGOs, Requested NGOs, Accepted NGOs from auth.db.
    Also fetch and provide donor's food donations from SQLite database.
    """
    import pprint
    # Get user info from database session if available
    db_session_id = session.get('db_session_id')
    print('[DEBUG] donor_dashboard session:', dict(session))
    if db_session_id:
        db_user = get_user_from_session(db_session_id)
        print('[DEBUG] donor_dashboard db_user:', db_user)
        if db_user:
            update_session_activity(db_session_id)
            user_info = db_user
            current_donor_name = db_user.get('user_name', None)
            current_donor_id = db_user.get('user_id', None)
        else:
            # Fallback to Flask session
            user_info = {
                'user_name': session.get('user_name', 'Food Donor'),
                'user_email': session.get('user_email', ''),
                'user_role': session.get('user_role', 'Donor'),
                'user_registration': session.get('user_registration', ''),
                'user_verified': session.get('user_verified', False)
            }
            current_donor_name = session.get('user_name', None)
            current_donor_id = session.get('user_id', None)
    else:
        # Fallback to Flask session
        user_info = {
            'user_name': session.get('user_name', 'Food Donor'),
            'user_email': session.get('user_email', ''),
            'user_role': session.get('user_role', 'Donor'),
            'user_registration': session.get('user_registration', ''),
            'user_verified': session.get('user_verified', False)
        }
        current_donor_name = session.get('user_name', None)
        current_donor_id = session.get('user_id', None)
    print('[DEBUG] donor_dashboard user_info:', user_info)
    print('[DEBUG] donor_dashboard current_donor_name:', current_donor_name)
    
    auth_conn = get_auth_db_connection()
    app_conn = get_db_connection()
    
    # Get donor's location for distance calculation
    donor_lat = None
    donor_lon = None
    if current_donor_id:
        donor_record = app_conn.execute('''
            SELECT pickup_lat, pickup_lon FROM food_donors WHERE id = ?
        ''', (current_donor_id,)).fetchone()
        if donor_record:
            donor_lat = donor_record['pickup_lat']
            donor_lon = donor_record['pickup_lon']

    # Get all registered NGOs from auth.db with location info
    all_ngos = auth_conn.execute('''
        SELECT id, name, email, registration_number, verified, location, city, latitude, longitude
        FROM users
        ORDER BY name
    ''').fetchall()

    # Get assigned/accepted NGOs for this donor from assignment database
    from database.assignment_db import get_assignment_db_connection
    assign_conn = get_assignment_db_connection()
    
    # Get requested NGOs (pending acceptance)
    requested_ngo_ids = []
    accepted_ngo_ids = []
    
    if current_donor_id:
        requested_assignments = assign_conn.execute('''
            SELECT DISTINCT ngo_id, ngo_name FROM ngo_assignments 
            WHERE food_donor_id = ? AND request_status = 'requested'
        ''', (current_donor_id,)).fetchall()
        requested_ngo_ids = [row['ngo_id'] for row in requested_assignments]
        
        accepted_assignments = assign_conn.execute('''
            SELECT DISTINCT ngo_id, ngo_name FROM ngo_assignments 
            WHERE food_donor_id = ? AND request_status = 'accepted'
        ''', (current_donor_id,)).fetchall()
        accepted_ngo_ids = [row['ngo_id'] for row in accepted_assignments]
    
    assign_conn.close()
    
    # Helper function to calculate distance between two coordinates
    import math
    def calculate_distance(lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return float('inf')  # Return infinity if coordinates are missing
        R = 6371  # Earth's radius in km
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    # Helper function to calculate approximate time (assuming 30 km/h average speed in city)
    def calculate_time(distance_km):
        if distance_km == float('inf'):
            return 'N/A'
        avg_speed = 30  # km/h
        time_hours = distance_km / avg_speed
        time_minutes = int(time_hours * 60)
        if time_minutes < 60:
            return f'{time_minutes} min'
        else:
            hours = time_minutes // 60
            mins = time_minutes % 60
            return f'{hours}h {mins}m'
    
    # Categorize NGOs with distance info
    available_ngos = []
    requested_ngos = []
    accepted_ngos = []
    
    for ngo in all_ngos:
        ngo_dict = dict(ngo)
        # Calculate distance from donor to NGO
        ngo_lat = ngo_dict.get('latitude')
        ngo_lon = ngo_dict.get('longitude')
        distance = calculate_distance(donor_lat, donor_lon, ngo_lat, ngo_lon)
        ngo_dict['distance_km'] = round(distance, 1) if distance != float('inf') else None
        ngo_dict['approx_time'] = calculate_time(distance)
        
        if ngo_dict['id'] in accepted_ngo_ids:
            accepted_ngos.append(ngo_dict)
        elif ngo_dict['id'] in requested_ngo_ids:
            requested_ngos.append(ngo_dict)
        else:
            available_ngos.append(ngo_dict)
    
    # Sort by distance (nearest first)
    available_ngos.sort(key=lambda x: x['distance_km'] if x['distance_km'] is not None else float('inf'))
    requested_ngos.sort(key=lambda x: x['distance_km'] if x['distance_km'] is not None else float('inf'))
    accepted_ngos.sort(key=lambda x: x['distance_km'] if x['distance_km'] is not None else float('inf'))

    auth_conn.close()
    app_conn.close()

    return render_template('Donor_dashboard.html', 
                         available_ngos=available_ngos, 
                         requested_ngos=requested_ngos, 
                         accepted_ngos=accepted_ngos,
                         **user_info)


@dashboard_bp.route('/ngo_dashboard')
def ngo_dashboard():
    """
    Render NGO dashboard showing Available and Accepted Food Donations from food_donors table.
    Sorted by distance (nearest first) and pickup time.
    """
    import math
    
    # Helper function to calculate distance between two coordinates
    def calculate_distance(lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return float('inf')
        R = 6371  # Earth's radius in km
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    # Helper function to calculate approximate time
    def calculate_time(distance_km):
        if distance_km == float('inf'):
            return 'N/A'
        avg_speed = 30  # km/h
        time_minutes = int((distance_km / avg_speed) * 60)
        if time_minutes < 60:
            return f'{time_minutes} min'
        else:
            hours = time_minutes // 60
            mins = time_minutes % 60
            return f'{hours}h {mins}m'
    
    # Get user info from database session if available
    db_session_id = session.get('db_session_id')
    if db_session_id:
        db_user = get_user_from_session(db_session_id)
        if db_user:
            update_session_activity(db_session_id)
            user_info = db_user
        else:
            user_info = {
                'user_name': session.get('user_name', ''),
                'user_email': session.get('user_email', ''),
                'user_role': session.get('user_role', 'NGO'),
                'user_registration': session.get('user_registration', ''),
                'user_verified': session.get('user_verified', False)
            }
    else:
        user_info = {
            'user_name': session.get('user_name', ''),
            'user_email': session.get('user_email', ''),
            'user_role': session.get('user_role', 'NGO'),
            'user_registration': session.get('user_registration', ''),
            'user_verified': session.get('user_verified', False)
        }
    
    from database.assignment_db import get_assignment_db_connection
    conn = get_assignment_db_connection()
    app_conn = get_db_connection()
    auth_conn = get_auth_db_connection()

    ngo_id = user_info.get('user_id') or session.get('user_id')
    
    # Get NGO's location for distance calculation
    ngo_lat = None
    ngo_lon = None
    if ngo_id:
        ngo_record = auth_conn.execute('''
            SELECT latitude, longitude FROM users WHERE id = ?
        ''', (ngo_id,)).fetchone()
        if ngo_record:
            ngo_lat = ngo_record['latitude']
            ngo_lon = ngo_record['longitude']
    
    # Get available donations - fetch from food_donors table with food details
    available_donations = app_conn.execute('''
        SELECT fd.id, fd.organization_name as food_donor_name, fd.food_type, fd.quantity,
               fd.ready_for_pickup_time as pickup_time, fd.pickup_location,
               fd.category as food_category, fd.cuisine_type, fd.spice_level,
               fd.status, fd.created_at, fd.phone, fd.email,
               fd.pickup_lat, fd.pickup_lon
        FROM food_donors fd
        WHERE fd.status = 'available' OR fd.status = 'pending'
        ORDER BY fd.ready_for_pickup_time ASC, fd.created_at DESC
    ''').fetchall()
    
    # Add distance and time info to each donation
    available_donations_dict = []
    for row in available_donations:
        donation = dict(row)
        donor_lat = donation.get('pickup_lat')
        donor_lon = donation.get('pickup_lon')
        distance = calculate_distance(ngo_lat, ngo_lon, donor_lat, donor_lon)
        donation['distance_km'] = round(distance, 1) if distance != float('inf') else None
        donation['approx_time'] = calculate_time(distance)
        available_donations_dict.append(donation)
    
    # Sort by distance first, then by pickup time
    available_donations_dict.sort(key=lambda x: (
        x['distance_km'] if x['distance_km'] is not None else float('inf'),
        x.get('pickup_time') or ''
    ))

    # Get accepted donations for this NGO
    accepted_donations = app_conn.execute('''
        SELECT fd.id, fd.organization_name as food_donor_name, fd.food_type, fd.quantity,
               fd.ready_for_pickup_time as pickup_time, fd.pickup_location,
               fd.category as food_category, fd.cuisine_type, fd.spice_level,
               fd.status, fd.created_at, fd.phone, fd.email,
               fd.pickup_lat, fd.pickup_lon,
               v.name as volunteer_name, v.contact as volunteer_contact
        FROM food_donors fd
        LEFT JOIN volunteers v ON fd.assigned_volunteer_id = v.id
        WHERE fd.status = 'accepted' AND fd.selected_ngo_id = ?
        ORDER BY fd.ready_for_pickup_time ASC, fd.created_at DESC
    ''', (ngo_id,)).fetchall() if ngo_id else []
    
    accepted_donations_dict = []
    for row in accepted_donations:
        donation = dict(row)
        donor_lat = donation.get('pickup_lat')
        donor_lon = donation.get('pickup_lon')
        distance = calculate_distance(ngo_lat, ngo_lon, donor_lat, donor_lon)
        donation['distance_km'] = round(distance, 1) if distance != float('inf') else None
        donation['approx_time'] = calculate_time(distance)
        accepted_donations_dict.append(donation)

    conn.close()
    app_conn.close()
    auth_conn.close()

    return render_template('NGO_dashboard.html', 
                         available_donations=available_donations_dict, 
                         accepted_donations=accepted_donations_dict,
                         **user_info)


@dashboard_bp.route('/ngo/my_accepted_donations')
def ngo_my_accepted_donations():
    """
    Render NGO's own accepted donations page.
    Shows only donations accepted by the current NGO (filtered by selected_ngo_id).
    For now, we'll show all accepted donations. In production, filter by logged-in NGO's ID.
    """
    # Get user info from database session if available
    db_session_id = session.get('db_session_id')
    if db_session_id:
        db_user = get_user_from_session(db_session_id)
        if db_user:
            update_session_activity(db_session_id)
            user_info = db_user
        else:
            # Fallback to Flask session
            user_info = {
                'user_name': session.get('user_name', ''),
                'user_email': session.get('user_email', ''),
                'user_role': session.get('user_role', 'NGO'),
                'user_registration': session.get('user_registration', ''),
                'user_verified': session.get('user_verified', False)
            }
    else:
        # Fallback to Flask session
        user_info = {
            'user_name': session.get('user_name', ''),
            'user_email': session.get('user_email', ''),
            'user_role': session.get('user_role', 'NGO'),
            'user_registration': session.get('user_registration', ''),
            'user_verified': session.get('user_verified', False)
        }
    
    conn = get_db_connection()
    
    # Get accepted donations with volunteer info
    # TODO: Filter by current NGO's ID when authentication is implemented
    # For now, showing all accepted donations
    accepted_donations = conn.execute('''
        SELECT fd.id, fd.organization_name as donor_name, fd.food_type, fd.quantity, 
               fd.ready_for_pickup_time as pickup_time, fd.pickup_location, 
               fd.category as food_category, fd.cuisine_type, fd.spice_level, 
               fd.status, fd.created_at, fd.selected_ngo_id,
               v.name as volunteer_name, v.contact as volunteer_contact
        FROM food_donors fd
        LEFT JOIN volunteers v ON fd.assigned_volunteer_id = v.id
        WHERE fd.status = 'accepted'
        ORDER BY fd.id DESC
    ''').fetchall()
    
    conn.close()
    
    accepted_donations_dict = [dict(row) for row in accepted_donations]
    
    return render_template('NGO_my_accepted_donations.html', 
                         accepted_donations=accepted_donations_dict,
                         **user_info)


@dashboard_bp.route('/donor/my_accepted_ngos')
def donor_my_accepted_ngos():
    """
    Render donor's accepted NGOs page with progress tracking.
    Shows donations that have been accepted by NGOs, with volunteer and location info.
    """
    # Get user info from database session if available
    db_session_id = session.get('db_session_id')
    if db_session_id:
        db_user = get_user_from_session(db_session_id)
        if db_user:
            update_session_activity(db_session_id)
            user_info = db_user
        else:
            # Fallback to Flask session
            user_info = {
                'user_name': session.get('user_name', 'Food Donor'),
                'user_email': session.get('user_email', ''),
                'user_role': session.get('user_role', 'Donor'),
                'user_registration': session.get('user_registration', ''),
                'user_verified': session.get('user_verified', False)
            }
    else:
        # Fallback to Flask session
        user_info = {
            'user_name': session.get('user_name', 'Food Donor'),
            'user_email': session.get('user_email', ''),
            'user_role': session.get('user_role', 'Donor'),
            'user_registration': session.get('user_registration', ''),
            'user_verified': session.get('user_verified', False)
        }
    
    conn = get_db_connection()
    
    # Get accepted donations with NGO and volunteer info
    accepted_donations = conn.execute('''
        SELECT fd.id, fd.organization_name as donor_name, fd.food_type, fd.quantity, 
               fd.ready_for_pickup_time as pickup_time, fd.pickup_location, 
               fd.category as food_category, fd.cuisine_type, fd.spice_level, 
               fd.status, fd.created_at, fd.selected_ngo_id,
               n.name as ngo_name, n.email as ngo_email, n.address as ngo_address,
               n.lat as ngo_lat, n.lon as ngo_lon,
               v.name as volunteer_name, v.contact as volunteer_contact,
               v.lat as volunteer_lat, v.lon as volunteer_lon
        FROM food_donors fd
        LEFT JOIN ngos n ON fd.selected_ngo_id = n.id
        LEFT JOIN volunteers v ON fd.assigned_volunteer_id = v.id
        WHERE fd.status = 'accepted' AND fd.selected_ngo_id IS NOT NULL
        ORDER BY fd.id DESC
    ''').fetchall()
    
    conn.close()
    
    accepted_donations_dict = [dict(row) for row in accepted_donations]
    
    return render_template('Donor_accepted_ngos.html', 
                         accepted_donations=accepted_donations_dict,
                         **user_info)


@dashboard_bp.route('/progress')
def progress():
    """
    Render progress tracking page with live map for food requests categorized by status.
    Shows only the assignments related to the logged-in user (NGO, Food Donor, or Volunteer).
    """

    from database.assignment_db import get_assignment_db_connection
    conn = get_assignment_db_connection()
    app_conn = get_db_connection()
    
    # Get user info from session
    user_name = session.get('user_name', '')
    user_email = session.get('user_email', '')
    user_role = session.get('user_role', '')
    user_id = session.get('user_id', '')
    
    # Get user's assignments from ngo_assignments table based on user role
    user_assignments = []
    if user_name or user_email:
        # Try to match by NGO name, food donor name, or volunteer name
        user_assignments = conn.execute("""
            SELECT a.*, 
                   CASE 
                       WHEN a.ngo_name = ? OR a.ngo_id = ? THEN 'ngo'
                       WHEN a.food_donor_name = ? OR a.food_donor_id = ? THEN 'donor'
                       WHEN a.volunteer_name = ? OR a.volunteer_id = ? THEN 'volunteer'
                       ELSE 'unknown'
                   END as user_match_type
            FROM ngo_assignments a
            WHERE a.ngo_name = ? OR a.ngo_id = ? OR a.food_donor_name = ? OR a.food_donor_id = ? OR a.volunteer_name = ? OR a.volunteer_id = ?
            ORDER BY a.assigned_at DESC
        """, (user_name, user_id, user_name, user_id, user_name, user_id, 
              user_name, user_id, user_name, user_id, user_name, user_id)).fetchall()
    
    user_assignments_list = [dict(row) for row in user_assignments]

    # Get food donor requests categorized by status - filtered for user if logged in
    if user_name or user_id:
        # Filter requests based on user being either the NGO or the food donor
        assigned_requests = conn.execute("""
            SELECT * FROM food_donor_requests 
            WHERE (status = 'pending' AND ngo_acceptance_status = 'pending')
            AND (ngo_name = ? OR ngo_id = ? OR food_donor_name = ? OR food_donor_id = ?)
            ORDER BY id DESC
        """, (user_name, user_id, user_name, user_id)).fetchall()
        collected_requests = conn.execute("""
            SELECT * FROM food_donor_requests 
            WHERE (status = 'accepted' AND ngo_acceptance_status = 'accepted')
            AND (ngo_name = ? OR ngo_id = ? OR food_donor_name = ? OR food_donor_id = ?)
            ORDER BY id DESC
        """, (user_name, user_id, user_name, user_id)).fetchall()
        in_transit_requests = conn.execute("""
            SELECT * FROM food_donor_requests 
            WHERE status = 'in_transit'
            AND (ngo_name = ? OR ngo_id = ? OR food_donor_name = ? OR food_donor_id = ?)
            ORDER BY id DESC
        """, (user_name, user_id, user_name, user_id)).fetchall()
        delivered_requests = conn.execute("""
            SELECT * FROM food_donor_requests 
            WHERE status = 'delivered'
            AND (ngo_name = ? OR ngo_id = ? OR food_donor_name = ? OR food_donor_id = ?)
            ORDER BY id DESC
        """, (user_name, user_id, user_name, user_id)).fetchall()
    else:
        # No user logged in - show all requests
        assigned_requests = conn.execute("""
            SELECT * FROM food_donor_requests WHERE status = 'pending' AND ngo_acceptance_status = 'pending' ORDER BY id DESC
        """).fetchall()
        collected_requests = conn.execute("""
            SELECT * FROM food_donor_requests WHERE status = 'accepted' AND ngo_acceptance_status = 'accepted' ORDER BY id DESC
        """).fetchall()
        in_transit_requests = conn.execute("""
            SELECT * FROM food_donor_requests WHERE status = 'in_transit' ORDER BY id DESC
        """).fetchall()
        delivered_requests = conn.execute("""
            SELECT * FROM food_donor_requests WHERE status = 'delivered' ORDER BY id DESC
        """).fetchall()

    # Get unique NGOs involved in these requests from app.db
    ngo_ids = list(set(req['ngo_id'] for req in assigned_requests + collected_requests + in_transit_requests + delivered_requests if req['ngo_id']))
    ngos = []
    if ngo_ids:
        placeholders = ','.join('?' * len(ngo_ids))
        ngos = app_conn.execute(f'''
            SELECT id, name, email
            FROM ngos
            WHERE id IN ({placeholders})
            ORDER BY name
        ''', ngo_ids).fetchall()

    # Get volunteers from user's assignments
    volunteer_ids = list(set(a['volunteer_id'] for a in user_assignments_list if a.get('volunteer_id')))
    volunteers = []
    if volunteer_ids:
        placeholders = ','.join('?' * len(volunteer_ids))
        volunteers = app_conn.execute(f'''
            SELECT * FROM volunteers WHERE id IN ({placeholders}) ORDER BY name
        ''', volunteer_ids).fetchall()

    # Get complaints/issues (placeholder - can be expanded)
    complaints = [{'message': 'No complaints reported', 'count': 0}]

    conn.close()
    app_conn.close()

    # Convert to list of dicts and add mock ETA
    def process_requests(rows):
        result = []
        for req in rows:
            req_dict = dict(req)
            if req_dict['status'] == 'assigned':
                req_dict['eta_minutes'] = 15
            elif req_dict['status'] == 'collected':
                req_dict['eta_minutes'] = 0
            elif req_dict['status'] == 'in_transit':
                req_dict['eta_minutes'] = 8
            elif req_dict['status'] == 'delivered':
                req_dict['eta_minutes'] = 0
            else:
                req_dict['eta_minutes'] = 0
            result.append(req_dict)
        return result

    assigned_requests_list = process_requests(assigned_requests)
    collected_requests_list = process_requests(collected_requests)
    in_transit_requests_list = process_requests(in_transit_requests)
    delivered_requests_list = process_requests(delivered_requests)

    # Convert NGO rows to dicts
    ngos_list = [dict(ngo) for ngo in ngos]
    volunteers_list = [dict(vol) for vol in volunteers]
    complaints_list = [dict(comp) for comp in complaints]

    return render_template('progress.html', 
                           assigned_requests=assigned_requests_list,
                           collected_requests=collected_requests_list,
                           in_transit_requests=in_transit_requests_list,
                           delivered_requests=delivered_requests_list,
                           ngos=ngos_list,
                           volunteers=volunteers_list,
                           complaints=complaints_list,
                           user_contact=session.get('user_contact'),
                           user_assignments=user_assignments_list,
                           user_name=user_name,
                           user_role=user_role)


@dashboard_bp.route('/volunteer_dashboard')
def volunteer_dashboard():
    """
    Render volunteer dashboard showing assigned food requests and delivery status.
    """
    # Get user info from session
    user_info = {
        'user_name': session.get('user_name', 'Volunteer'),
        'user_email': session.get('user_email', ''),
        'user_role': session.get('user_role', 'Volunteer'),
        'user_verified': session.get('user_verified', False)
    }

    conn = get_db_connection()

    # Get assigned food requests for this volunteer
    assigned_requests = conn.execute('''
        SELECT fr.id, fr.donor_name, fr.food_type, fr.quantity, fr.pickup_location,
               fr.pickup_lat, fr.pickup_lon, fr.pickup_time, fr.status,
               n.name as ngo_name, n.address as ngo_address, n.lat as ngo_lat, n.lon as ngo_lon
        FROM food_requests fr
        LEFT JOIN ngos n ON fr.ngo_id = n.id
        WHERE fr.assigned_volunteer_id = ? AND fr.status IN ('assigned', 'collected', 'in_transit', 'delivered')
        ORDER BY fr.id DESC
    ''', (session.get('user_id'),)).fetchall()

    # Get completed deliveries for this volunteer
    completed_deliveries = conn.execute('''
        SELECT fr.id, fr.donor_name, fr.food_type, fr.quantity, fr.pickup_location,
               fr.pickup_time, fr.status, fr.completed_at,
               n.name as ngo_name, n.address as ngo_address
        FROM food_requests fr
        LEFT JOIN ngos n ON fr.ngo_id = n.id
        WHERE fr.assigned_volunteer_id = ? AND fr.status = 'delivered'
        ORDER BY fr.completed_at DESC
        LIMIT 10
    ''', (session.get('user_id'),)).fetchall()

    conn.close()

    # Convert to dicts
    assigned_requests_dict = [dict(row) for row in assigned_requests]
    completed_deliveries_dict = [dict(row) for row in completed_deliveries]

    return render_template('volunteers/volunteer_dashboard.html',
                         assigned_requests=assigned_requests_dict,
                         completed_deliveries=completed_deliveries_dict,
                         **user_info)


@dashboard_bp.route('/mark_food_packed', methods=['POST'])
def mark_food_packed():
    """
    Mark food as packed by the food donor.
    This triggers the automatic volunteer collection step.
    """
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    
    if not assignment_id:
        return jsonify({'success': False, 'error': 'Missing assignment_id'}), 400
    
    try:
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        
        # Mark food as packed
        conn.execute('''
            UPDATE ngo_assignments 
            SET food_packed = 1, food_packed_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (assignment_id,))
        conn.commit()
        
        # Auto-trigger volunteer collection (since volunteers are dummy for now)
        # No delay needed - simulate instant assignment for demo purposes
        
        # Assign a dummy volunteer and mark as collected
        app_conn = get_db_connection()
        volunteer = app_conn.execute('SELECT id, name FROM volunteers WHERE is_available = 1 LIMIT 1').fetchone()
        app_conn.close()
        
        if volunteer:
            # Auto-assign volunteer, mark as collected and reached NGO
            conn.execute('''
                UPDATE ngo_assignments 
                SET volunteer_id = ?, volunteer_name = ?, 
                    volunteer_allocated_time = CURRENT_TIMESTAMP,
                    volunteer_collected = 1, volunteer_collected_time = CURRENT_TIMESTAMP,
                    reached_ngo = 1, reached_ngo_time = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (volunteer['id'], volunteer['name'], assignment_id))
            conn.commit()
        
        conn.close()
        return jsonify({'success': True, 'message': 'Food marked as packed and volunteer assigned'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/mark_donation_complete', methods=['POST'])
def mark_donation_complete():
    """
    Mark donation as complete by the NGO.
    """
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    
    if not assignment_id:
        return jsonify({'success': False, 'error': 'Missing assignment_id'}), 400
    
    try:
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        
        # Mark as completed
        conn.execute('''
            UPDATE ngo_assignments 
            SET completed = 1, completed_time = CURRENT_TIMESTAMP, request_status = 'completed'
            WHERE id = ?
        ''', (assignment_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Donation marked as complete'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/get_assignment_progress/<int:assignment_id>')
def get_assignment_progress(assignment_id):
    """
    Get the progress of a specific assignment for live tracking.
    """
    try:
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        
        assignment = conn.execute('''
            SELECT * FROM ngo_assignments WHERE id = ?
        ''', (assignment_id,)).fetchone()
        
        conn.close()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Assignment not found'}), 404
        
        assignment_dict = dict(assignment)
        
        # Calculate progress steps
        steps = {
            'food_packed': bool(assignment_dict.get('food_packed', 0)),
            'food_packed_time': assignment_dict.get('food_packed_time'),
            'volunteer_collected': bool(assignment_dict.get('volunteer_collected', 0)),
            'volunteer_collected_time': assignment_dict.get('volunteer_collected_time'),
            'reached_ngo': bool(assignment_dict.get('reached_ngo', 0)),
            'reached_ngo_time': assignment_dict.get('reached_ngo_time'),
            'completed': bool(assignment_dict.get('completed', 0)),
            'completed_time': assignment_dict.get('completed_time'),
            'volunteer_name': assignment_dict.get('volunteer_name'),
            'request_status': assignment_dict.get('request_status')
        }
        
        return jsonify({'success': True, 'progress': steps, 'assignment': assignment_dict})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/donor/my_assignments')
def donor_my_assignments():
    """
    Get assignments for the current food donor with tracking progress.
    """
    donor_id = session.get('user_id')
    donor_name = session.get('user_name')
    
    if not donor_id and not donor_name:
        return jsonify({'success': False, 'error': 'Please login as a food donor first'}), 401
    
    try:
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        
        # Get all assignments for this donor
        assignments = conn.execute('''
            SELECT * FROM ngo_assignments 
            WHERE food_donor_id = ? OR food_donor_name = ?
            ORDER BY assigned_at DESC
        ''', (donor_id, donor_name)).fetchall()
        
        conn.close()
        
        assignments_list = [dict(a) for a in assignments]
        
        return jsonify({'success': True, 'assignments': assignments_list})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/ngo/my_requests')
def ngo_my_requests():
    """
    Get donation requests for the current NGO.
    """
    ngo_id = session.get('user_id')
    ngo_name = session.get('user_name')
    
    if not ngo_id and not ngo_name:
        return jsonify({'success': False, 'error': 'Please login as an NGO first'}), 401
    
    try:
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        
        # Get all assignments for this NGO
        assignments = conn.execute('''
            SELECT * FROM ngo_assignments 
            WHERE ngo_id = ? OR ngo_name = ?
            ORDER BY assigned_at DESC
        ''', (ngo_id, ngo_name)).fetchall()
        
        conn.close()
        
        assignments_list = [dict(a) for a in assignments]
        
        return jsonify({'success': True, 'assignments': assignments_list})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/ngo/accept_donor_request', methods=['POST'])
def ngo_accept_donor_request():
    """
    NGO accepts a food donor's request.
    """
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    
    if not assignment_id:
        return jsonify({'success': False, 'error': 'Missing assignment_id'}), 400
    
    try:
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        
        # Update assignment status to accepted
        conn.execute('''
            UPDATE ngo_assignments 
            SET request_status = 'accepted', acceptance_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (assignment_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Request accepted'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


