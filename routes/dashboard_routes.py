"""
Dashboard routes for Donor and NGO dashboards
"""
from flask import Blueprint, render_template, session, request, jsonify
from db import get_db_connection, get_auth_db_connection
from database.session_manager import get_user_from_session, update_session_activity
import random
import math

dashboard_bp = Blueprint('dashboard', __name__)

# Progress step constants
PROGRESS_STEP_NONE = 0
PROGRESS_STEP_FOOD_PACKED = 1
PROGRESS_STEP_VOLUNTEER_ASSIGNED = 2
PROGRESS_STEP_NEAR_NGO = 3
PROGRESS_STEP_DELIVERED = 4

# Random volunteer names for testing
RANDOM_VOLUNTEER_NAMES = [
    "Arun Kumar", "Priya Sharma", "Rahul Verma", "Sneha Reddy", 
    "Vikram Singh", "Anita Patel", "Rajesh Menon", "Kavitha Nair",
    "Suresh Babu", "Lakshmi Iyer", "Karthik Rajan", "Deepa Krishnan",
    "Manoj Kumar", "Shanti Devi", "Ganesh Pillai", "Meera Gopal"
]

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula (returns km)"""
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def assign_nearest_volunteer(pickup_lat, pickup_lon, max_radius_km=10):
    """
    Assign the nearest available volunteer within radius using Haversine formula.
    Returns volunteer dict or None if no volunteers available.
    """
    conn = get_db_connection()
    volunteers = conn.execute('''
        SELECT * FROM volunteers WHERE is_available = 1
    ''').fetchall()
    
    best_volunteer = None
    min_distance = float('inf')
    
    for vol in volunteers:
        if vol['lat'] and vol['lon']:
            distance = haversine(pickup_lat, pickup_lon, vol['lat'], vol['lon'])
            if distance <= max_radius_km and distance < min_distance:
                min_distance = distance
                best_volunteer = dict(vol)
                best_volunteer['distance_km'] = round(distance, 2)
    
    # If no real volunteer found, create a mock volunteer with random name
    if not best_volunteer:
        best_volunteer = {
            'id': random.randint(100, 999),
            'name': random.choice(RANDOM_VOLUNTEER_NAMES),
            'contact': f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}",
            'lat': pickup_lat + random.uniform(-0.01, 0.01),
            'lon': pickup_lon + random.uniform(-0.01, 0.01),
            'distance_km': round(random.uniform(0.5, 5.0), 2),
            'is_mock': True
        }
    
    conn.close()
    return best_volunteer

@dashboard_bp.route('/accept_ngo', methods=['POST'])
def accept_ngo():
    """
    Backend route for donor accepting an NGO. Creates assignment and food_donor_request records.
    This moves the NGO from 'Available' to 'Requested' for the donor.
    """
    data = request.get_json()
    print('[DEBUG] /accept_ngo incoming data:', data)
    ngo_id = data.get('ngo_id')
    ngo_name = data.get('ngo_name')
    # Get donor info from session
    print('[DEBUG] Session in /accept_ngo:', dict(session))
    donor_name = session.get('user_name')
    donor_id = session.get('user_id')
    missing = []
    if not ngo_id:
        missing.append('ngo_id')
    if not ngo_name:
        missing.append('ngo_name')
    if not donor_name:
        missing.append('donor_name')
    if not donor_id:
        missing.append('donor_id')
    if missing:
        return jsonify({'success': False, 'error': f'Missing required fields: {", ".join(missing)}'}), 400
    try:
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        cursor = conn.cursor()
        
        # Insert new assignment record with status 'requested'
        cursor.execute('''
            INSERT INTO ngo_assignments (food_donor_id, food_donor_name, ngo_id, ngo_name, request_status, assigned_at)
            VALUES (?, ?, ?, ?, 'requested', CURRENT_TIMESTAMP)
        ''', (donor_id, donor_name, ngo_id, ngo_name))
        assignment_id = cursor.lastrowid
        
        # Also create a food_donor_request for the NGO to see
        cursor.execute('''
            INSERT INTO food_donor_requests (assignment_id, food_donor_id, food_donor_name, ngo_id, ngo_name, status, ngo_acceptance_status)
            VALUES (?, ?, ?, ?, ?, 'pending', 'pending')
        ''', (assignment_id, donor_id, donor_name, ngo_id, ngo_name))
        
        conn.commit()
        conn.close()
        print(f'[DEBUG] Assignment created: donor_id={donor_id}, ngo_id={ngo_id}, assignment_id={assignment_id}')
        return jsonify({'success': True, 'assignment_id': assignment_id, 'message': 'Request sent to NGO'})
    except Exception as e:
        import traceback
        print('[ERROR] Exception in /accept_ngo:')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# Random volunteer phone numbers and vehicle types for testing
RANDOM_PHONES = [
    "+91 98765 43210", "+91 87654 32109", "+91 76543 21098",
    "+91 65432 10987", "+91 54321 09876", "+91 43210 98765"
]
RANDOM_VEHICLES = ["Bike", "Scooty", "Car", "Van", "Auto Rickshaw"]


@dashboard_bp.route('/ngo_accept_donation', methods=['POST'])
def ngo_accept_donation():
    """NGO accepts a food donation request and assigns a volunteer"""
    data = request.get_json()
    print('[DEBUG] /ngo_accept_donation incoming data:', data)
    request_id = data.get('request_id')
    if not request_id:
        return jsonify({'success': False, 'error': 'Missing request_id'}), 400
    import traceback
    try:
        from database.assignment_db import get_assignment_db_connection
        
        # Get the request details to find pickup location
        conn = get_assignment_db_connection()
        req = conn.execute('SELECT * FROM food_donor_requests WHERE id = ?', (request_id,)).fetchone()
        
        # Assign a volunteer (using random names for now)
        volunteer_name = random.choice(RANDOM_VOLUNTEER_NAMES)
        volunteer_id = random.randint(100, 999)
        volunteer_phone = random.choice(RANDOM_PHONES)
        volunteer_vehicle = random.choice(RANDOM_VEHICLES)
        
        # Update the request with volunteer info and acceptance
        # Also set progress_step to PROGRESS_STEP_FOOD_PACKED (Food packed & ready)
        conn.execute('''
            UPDATE food_donor_requests 
            SET status = 'accepted', ngo_acceptance_status = 'accepted', 
                volunteer_id = ?, volunteer_name = ?, 
                volunteer_allocated_time = CURRENT_TIMESTAMP,
                progress_step = ?
            WHERE id = ?
        ''', (volunteer_id, volunteer_name, PROGRESS_STEP_FOOD_PACKED, request_id))
        
        # Also update the parent assignment
        conn.execute('''
            UPDATE ngo_assignments 
            SET request_status = 'accepted', acceptance_time = CURRENT_TIMESTAMP,
                volunteer_id = ?, volunteer_name = ?,
                volunteer_allocated_time = CURRENT_TIMESTAMP,
                volunteer_phone = ?, volunteer_vehicle = ?,
                progress_step = ?
            WHERE id = (SELECT assignment_id FROM food_donor_requests WHERE id = ?)
        ''', (volunteer_id, volunteer_name, volunteer_phone, volunteer_vehicle, PROGRESS_STEP_FOOD_PACKED, request_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'volunteer_name': volunteer_name,
            'volunteer_id': volunteer_id,
            'volunteer_phone': volunteer_phone,
            'volunteer_vehicle': volunteer_vehicle
        })
    except Exception as e:
        print('[ERROR] Exception in ngo_accept_donation:')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/update_progress_step', methods=['POST'])
def update_progress_step():
    """Update the progress step for a donation request"""
    data = request.get_json()
    request_id = data.get('request_id')
    step = data.get('step')
    
    if not request_id or step is None:
        return jsonify({'success': False, 'error': 'Missing request_id or step'}), 400
    
    try:
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        
        # Update progress step
        conn.execute('''
            UPDATE food_donor_requests SET progress_step = ? WHERE id = ?
        ''', (step, request_id))
        
        conn.execute('''
            UPDATE ngo_assignments SET progress_step = ?
            WHERE id = (SELECT assignment_id FROM food_donor_requests WHERE id = ?)
        ''', (step, request_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'step': step})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/donor/requested_ngos')
def donor_requested_ngos():
    """
    Render page showing all NGOs that this food donor has requested.
    """
    current_donor_id = session.get('user_id')
    current_donor_name = session.get('user_name')
    
    user_info = {
        'user_name': session.get('user_name', 'Food Donor'),
        'user_email': session.get('user_email', ''),
        'user_role': session.get('user_role', 'Donor'),
    }
    
    requested_ngos = []
    
    if current_donor_id:
        from database.assignment_db import get_assignment_db_connection
        assign_conn = get_assignment_db_connection()
        
        # Get all NGO requests for this donor
        requests = assign_conn.execute('''
            SELECT a.ngo_id, a.ngo_name, a.request_status, a.assigned_at as request_time,
                   a.volunteer_name, a.volunteer_id, a.acceptance_time,
                   r.status, r.ngo_acceptance_status
            FROM ngo_assignments a
            LEFT JOIN food_donor_requests r ON a.id = r.assignment_id
            WHERE a.food_donor_id = ?
            ORDER BY a.assigned_at DESC
        ''', (current_donor_id,)).fetchall()
        
        assign_conn.close()
        
        # Get NGO details from app.db
        app_conn = get_db_connection()
        for req in requests:
            ngo = app_conn.execute('''
                SELECT id, name, email, address, registration_number
                FROM ngos WHERE id = ?
            ''', (req['ngo_id'],)).fetchone()
            
            if ngo:
                ngo_dict = dict(ngo)
                ngo_dict['request_time'] = req['request_time']
                ngo_dict['volunteer_name'] = req['volunteer_name']
                
                # Determine status
                if req['ngo_acceptance_status'] == 'accepted' or req['request_status'] == 'accepted':
                    ngo_dict['status'] = 'accepted'
                    ngo_dict['status_display'] = 'Accepted by NGO'
                else:
                    ngo_dict['status'] = 'pending'
                    ngo_dict['status_display'] = 'Pending NGO Approval'
                
                requested_ngos.append(ngo_dict)
        
        app_conn.close()
    
    return render_template('food_donor_requested.html',
                         requested_ngos=requested_ngos,
                         **user_info)


@dashboard_bp.route('/donor_dashboard')
def donor_dashboard():
    from flask import session
    print('[DEBUG] Session at donor_dashboard:', dict(session))
    """
    Render donor dashboard showing Available NGOs, Requested NGOs, Accepted NGOs.
    """
    # Get user info from database session if available
    db_session_id = session.get('db_session_id')
    current_donor_id = session.get('user_id')
    current_donor_name = session.get('user_name')
    
    if db_session_id:
        db_user = get_user_from_session(db_session_id)
        if db_user:
            update_session_activity(db_session_id)
            user_info = db_user
            current_donor_name = db_user.get('user_name', None)
            current_donor_id = db_user.get('user_id', None)
        else:
            user_info = {
                'user_name': session.get('user_name', 'Food Donor'),
                'user_email': session.get('user_email', ''),
                'user_role': session.get('user_role', 'Donor'),
                'user_registration': session.get('user_registration', ''),
                'user_verified': session.get('user_verified', False)
            }
    else:
        user_info = {
            'user_name': session.get('user_name', 'Food Donor'),
            'user_email': session.get('user_email', ''),
            'user_role': session.get('user_role', 'Donor'),
            'user_registration': session.get('user_registration', ''),
            'user_verified': session.get('user_verified', False)
        }
    
    # Get NGOs from app.db
    app_conn = get_db_connection()
    all_ngos = app_conn.execute('''
        SELECT id, name, email, registration_number, verified, lat, lon, address
        FROM ngos ORDER BY name
    ''').fetchall()
    app_conn.close()
    
    # Get assignments from assignment.db to categorize NGOs
    from database.assignment_db import get_assignment_db_connection
    assign_conn = get_assignment_db_connection()
    
    # Get requested NGOs (donor has requested but NGO hasn't accepted yet)
    requested_assignments = assign_conn.execute('''
        SELECT DISTINCT ngo_id, ngo_name FROM ngo_assignments 
        WHERE food_donor_id = ? AND request_status = 'requested'
    ''', (current_donor_id,)).fetchall() if current_donor_id else []
    requested_ngo_ids = set(a['ngo_id'] for a in requested_assignments)
    
    # Get accepted NGOs (NGO has accepted the request)
    accepted_assignments = assign_conn.execute('''
        SELECT a.ngo_id, a.ngo_name, a.volunteer_name, a.volunteer_id, 
               a.acceptance_time, r.status as request_status
        FROM ngo_assignments a
        LEFT JOIN food_donor_requests r ON a.id = r.assignment_id
        WHERE a.food_donor_id = ? AND (a.request_status = 'accepted' OR r.status = 'accepted')
    ''', (current_donor_id,)).fetchall() if current_donor_id else []
    accepted_ngo_ids = set(a['ngo_id'] for a in accepted_assignments)
    
    assign_conn.close()
    
    # Categorize NGOs
    available_ngos = []
    requested_ngos = []
    accepted_ngos = []
    
    for ngo in all_ngos:
        ngo_dict = dict(ngo)
        if ngo_dict['id'] in accepted_ngo_ids:
            # Find volunteer info for this NGO
            for a in accepted_assignments:
                if a['ngo_id'] == ngo_dict['id']:
                    ngo_dict['volunteer_name'] = a['volunteer_name']
                    ngo_dict['acceptance_time'] = a['acceptance_time']
                    break
            accepted_ngos.append(ngo_dict)
        elif ngo_dict['id'] in requested_ngo_ids:
            requested_ngos.append(ngo_dict)
        else:
            available_ngos.append(ngo_dict)

    return render_template('Donor_dashboard.html', 
                         available_ngos=available_ngos, 
                         requested_ngos=requested_ngos, 
                         accepted_ngos=accepted_ngos,
                         **user_info)


@dashboard_bp.route('/ngo_dashboard')
def ngo_dashboard():
    """
    Render NGO dashboard showing Food Donors who requested this NGO.
    """
    # Get user info from database session if available
    db_session_id = session.get('db_session_id')
    ngo_id = session.get('user_id')
    ngo_email = session.get('user_email')
    
    if db_session_id:
        db_user = get_user_from_session(db_session_id)
        if db_user:
            update_session_activity(db_session_id)
            user_info = db_user
            ngo_id = db_user.get('user_id')
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
    
    # If no ngo_id from session, try to look up by email
    if not ngo_id and ngo_email:
        app_conn = get_db_connection()
        ngo_row = app_conn.execute('SELECT id FROM ngos WHERE email = ?', (ngo_email,)).fetchone()
        if ngo_row:
            ngo_id = ngo_row['id']
        app_conn.close()
    
    from database.assignment_db import get_assignment_db_connection
    conn = get_assignment_db_connection()

    # Get pending food donor requests for this NGO
    available_donations = []
    accepted_donations = []
    
    if ngo_id:
        # Pending requests
        available_donations = conn.execute('''
            SELECT r.id, r.food_donor_id, r.food_donor_name, r.ngo_id, r.ngo_name, 
                   r.status, r.ngo_acceptance_status, r.request_time,
                   a.assigned_at
            FROM food_donor_requests r
            LEFT JOIN ngo_assignments a ON r.assignment_id = a.id
            WHERE r.ngo_id = ? AND r.ngo_acceptance_status = 'pending'
            ORDER BY r.request_time DESC
        ''', (ngo_id,)).fetchall()
        
        # Accepted requests with volunteer info
        accepted_donations = conn.execute('''
            SELECT r.id, r.food_donor_id, r.food_donor_name, r.ngo_id, r.ngo_name,
                   r.status, r.ngo_acceptance_status, r.volunteer_id, r.volunteer_name,
                   r.volunteer_allocated_time, a.acceptance_time
            FROM food_donor_requests r
            LEFT JOIN ngo_assignments a ON r.assignment_id = a.id
            WHERE r.ngo_id = ? AND r.ngo_acceptance_status = 'accepted'
            ORDER BY a.acceptance_time DESC
        ''', (ngo_id,)).fetchall()
    
    conn.close()

    available_donations_dict = [dict(row) for row in available_donations]
    accepted_donations_dict = [dict(row) for row in accepted_donations]

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
    """

    from database.assignment_db import get_assignment_db_connection
    conn = get_assignment_db_connection()

    # Get food donor requests categorized by status
    assigned_requests = conn.execute("""
        SELECT * FROM food_donor_requests WHERE status = 'pending' AND ngo_acceptance_status = 'pending' ORDER BY id DESC
    """).fetchall()
    collected_requests = conn.execute("""
        SELECT r.*, a.volunteer_phone, a.volunteer_vehicle 
        FROM food_donor_requests r
        LEFT JOIN ngo_assignments a ON r.assignment_id = a.id
        WHERE r.status = 'accepted' AND r.ngo_acceptance_status = 'accepted' 
        ORDER BY r.id DESC
    """).fetchall()
    in_transit_requests = conn.execute("""
        SELECT r.*, a.volunteer_phone, a.volunteer_vehicle 
        FROM food_donor_requests r
        LEFT JOIN ngo_assignments a ON r.assignment_id = a.id
        WHERE r.status = 'in_transit' 
        ORDER BY r.id DESC
    """).fetchall()
    delivered_requests = conn.execute("""
        SELECT r.*, a.volunteer_phone, a.volunteer_vehicle 
        FROM food_donor_requests r
        LEFT JOIN ngo_assignments a ON r.assignment_id = a.id
        WHERE r.status = 'delivered' 
        ORDER BY r.id DESC
    """).fetchall()

    # Get unique NGOs involved in these requests - from app.db
    ngo_ids = list(set(req['ngo_id'] for req in assigned_requests + collected_requests + in_transit_requests + delivered_requests if req['ngo_id']))
    ngos = []
    if ngo_ids:
        app_conn = get_db_connection()
        placeholders = ','.join('?' * len(ngo_ids))
        ngos = app_conn.execute(f'''
            SELECT id, name, email
            FROM ngos
            WHERE id IN ({placeholders})
            ORDER BY name
        ''', ngo_ids).fetchall()
        app_conn.close()

    # Get all volunteers for admin view - from app.db
    app_conn = get_db_connection()
    volunteers = app_conn.execute('''
        SELECT * FROM volunteers ORDER BY name
    ''').fetchall()
    app_conn.close()

    # Get all food donors (from food_donor_requests table)
    donors = conn.execute('''
        SELECT DISTINCT food_donor_name, COUNT(*) as total_donations,
               COUNT(CASE WHEN status IN ('pending', 'accepted', 'in_transit', 'delivered') THEN 1 END) as active_donations
        FROM food_donor_requests
        GROUP BY food_donor_name
        ORDER BY food_donor_name
    ''').fetchall()

    # Get complaints/issues (placeholder - can be expanded)
    complaints = [{'message': 'No complaints reported', 'count': 0}]

    conn.close()

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
    donors_list = [dict(don) for don in donors]
    complaints_list = [dict(comp) for comp in complaints]

    # Fetch assignment data for the logged-in user from assignment.db
    user_email = session.get('user_email')
    user_assignments = []
    if user_email:
        try:
            from database.get_user_assignments import get_user_assignments
            user_assignments = get_user_assignments(user_email)
        except Exception as e:
            user_assignments = []
    return render_template('progress_tracking.html', 
                           assigned_requests=assigned_requests_list,
                           collected_requests=collected_requests_list,
                           in_transit_requests=in_transit_requests_list,
                           delivered_requests=delivered_requests_list,
                           ngos=ngos_list,
                           volunteers=volunteers_list,
                           donors=donors_list,
                           complaints=complaints_list,
                           user_contact=session.get('user_contact'),
                           user_assignments=user_assignments)


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

    return render_template('volunteer_dashboard.html',
                         assigned_requests=assigned_requests_dict,
                         completed_deliveries=completed_deliveries_dict,
                         **user_info)

