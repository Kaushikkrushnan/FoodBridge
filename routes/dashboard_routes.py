"""
Dashboard routes for Donor and NGO dashboards
"""
from flask import Blueprint, render_template, session, request, jsonify
from db import get_db_connection, get_auth_db_connection
from database.session_manager import get_user_from_session, update_session_activity
import math

dashboard_bp = Blueprint('dashboard', __name__)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate approximate distance between two coordinates using Haversine formula.
    Returns distance in kilometers.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999.0  # Return large but finite value if coordinates are missing
    
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


@dashboard_bp.route('/accept_ngo', methods=['POST'])
def accept_ngo():
    """
    Backend route for donor requesting pickup from an NGO. Creates assignment and request records.
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
        # Insert assignment into assignment_db
        from database.assignment_db import get_assignment_db_connection
        conn = get_assignment_db_connection()
        cursor = conn.cursor()
        
        # Insert new assignment record
        cursor.execute('''
            INSERT INTO ngo_assignments (food_donor_id, food_donor_name, ngo_id, ngo_name, assigned_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (donor_id, donor_name, ngo_id, ngo_name))
        assignment_id = cursor.lastrowid
        
        # Also insert into food_donor_requests with pending status
        cursor.execute('''
            INSERT INTO food_donor_requests (assignment_id, food_donor_id, food_donor_name, ngo_id, ngo_name, status, ngo_acceptance_status, request_time)
            VALUES (?, ?, ?, ?, ?, 'pending', 'pending', CURRENT_TIMESTAMP)
        ''', (assignment_id, donor_id, donor_name, ngo_id, ngo_name))
        
        conn.commit()
        conn.close()
        
        print(f'[DEBUG] Assignment and request created: donor_id={donor_id}, ngo_id={ngo_id}, assignment_id={assignment_id}')
        
        # Send SMS notification to donor
        try:
            app_conn = get_db_connection()
            donor = app_conn.execute('SELECT phone FROM food_donors WHERE id = ?', (donor_id,)).fetchone()
            app_conn.close()
            if donor and donor['phone']:
                from utils.sms_service import notify_request_sent
                notify_request_sent(donor['phone'], ngo_name)
        except Exception as sms_error:
            print(f'[SMS] Failed to send request notification: {sms_error}')
        
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
        from database.assignment_db import accept_food_donation_request, get_assignment_db_connection
        accept_food_donation_request(request_id)
        
        # Get donor info for SMS notification
        try:
            assign_conn = get_assignment_db_connection()
            request_info = assign_conn.execute('''
                SELECT fdr.food_donor_id, fdr.food_donor_name, fdr.ngo_name
                FROM food_donor_requests fdr
                WHERE fdr.id = ?
            ''', (request_id,)).fetchone()
            assign_conn.close()
            
            if request_info:
                # Get donor phone from app.db
                app_conn = get_db_connection()
                donor = app_conn.execute('SELECT phone FROM food_donors WHERE id = ?', 
                                        (request_info['food_donor_id'],)).fetchone()
                app_conn.close()
                
                if donor and donor['phone']:
                    from utils.sms_service import notify_ngo_accepted
                    notify_ngo_accepted(
                        donor_phone=donor['phone'],
                        ngo_name=request_info['ngo_name']
                    )
        except Exception as sms_error:
            print(f'[SMS] Failed to send acceptance notification: {sms_error}')
        
        return jsonify({'success': True})
    except Exception as e:
        print('[ERROR] Exception in ngo_accept_donation:')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/mark_donation_completed', methods=['POST'])
def mark_donation_completed():
    """
    Mark a donation as completed. Updates status and sends SMS notifications.
    Expects JSON: { 'request_id': ... }
    """
    data = request.get_json()
    request_id = data.get('request_id')
    
    if not request_id:
        return jsonify({'success': False, 'error': 'Missing request_id'}), 400
    
    try:
        from database.assignment_db import get_assignment_db_connection
        assign_conn = get_assignment_db_connection()
        
        # Update status to delivered/completed
        assign_conn.execute('''
            UPDATE food_donor_requests
            SET status = 'delivered', ngo_acceptance_status = 'completed'
            WHERE id = ?
        ''', (request_id,))
        assign_conn.commit()
        
        # Get request info for SMS
        request_info = assign_conn.execute('''
            SELECT fdr.food_donor_id, fdr.food_donor_name, fdr.ngo_name, fdr.ngo_id
            FROM food_donor_requests fdr
            WHERE fdr.id = ?
        ''', (request_id,)).fetchone()
        assign_conn.close()
        
        if request_info:
            # Get donor and NGO phone numbers
            app_conn = get_db_connection()
            donor = app_conn.execute('SELECT phone FROM food_donors WHERE id = ?', 
                                    (request_info['food_donor_id'],)).fetchone()
            app_conn.close()
            
            # Send completion SMS
            if donor and donor['phone']:
                try:
                    from utils.sms_service import notify_donation_completed
                    notify_donation_completed(
                        donor_phone=donor['phone'],
                        ngo_phone=None,  # Add NGO phone if available
                        donor_name=request_info['food_donor_name'],
                        ngo_name=request_info['ngo_name']
                    )
                except Exception as sms_error:
                    print(f'[SMS] Failed to send completion notification: {sms_error}')
        
        return jsonify({'success': True, 'message': 'Donation marked as completed'})
    except Exception as e:
        import traceback
        print('[ERROR] Exception in mark_donation_completed:')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/update_tracking_status', methods=['POST'])
def update_tracking_status():
    """
    Update the tracking status of a donation.
    Expects JSON: { 'request_id': ..., 'status': 'packed' | 'collected' | 'near_ngo' | 'completed' }
    """
    data = request.get_json()
    request_id = data.get('request_id')
    new_status = data.get('status')
    
    valid_statuses = ['packed', 'collected', 'in_transit', 'near_ngo', 'delivered', 'completed']
    
    if not request_id or not new_status:
        return jsonify({'success': False, 'error': 'Missing request_id or status'}), 400
    
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
    
    try:
        from database.assignment_db import get_assignment_db_connection
        assign_conn = get_assignment_db_connection()
        
        # Update status
        assign_conn.execute('''
            UPDATE food_donor_requests
            SET status = ?
            WHERE id = ?
        ''', (new_status, request_id))
        assign_conn.commit()
        
        # Get request info for SMS
        request_info = assign_conn.execute('''
            SELECT fdr.food_donor_id, fdr.food_donor_name, fdr.ngo_name, fdr.ngo_id
            FROM food_donor_requests fdr
            WHERE fdr.id = ?
        ''', (request_id,)).fetchone()
        assign_conn.close()
        
        if request_info:
            app_conn = get_db_connection()
            donor = app_conn.execute('SELECT phone FROM food_donors WHERE id = ?', 
                                    (request_info['food_donor_id'],)).fetchone()
            app_conn.close()
            
            # Send appropriate SMS based on status
            if donor and donor['phone']:
                try:
                    from utils.sms_service import send_sms
                    status_messages = {
                        'packed': f"FoodBridge: Food from {request_info['food_donor_name']} is packed and ready for pickup.",
                        'collected': f"FoodBridge: Volunteer has collected food from {request_info['food_donor_name']}.",
                        'in_transit': f"FoodBridge: Food is on the way to {request_info['ngo_name']}.",
                        'near_ngo': f"FoodBridge: Food is near {request_info['ngo_name']}. Delivery soon!",
                        'delivered': f"FoodBridge: Food delivered to {request_info['ngo_name']}. Thank you!",
                        'completed': f"FoodBridge: Donation from {request_info['food_donor_name']} completed successfully!"
                    }
                    message = status_messages.get(new_status)
                    if message:
                        send_sms(donor['phone'], message)
                except Exception as sms_error:
                    print(f'[SMS] Failed to send status update: {sms_error}')
        
        return jsonify({'success': True, 'status': new_status})
    except Exception as e:
        import traceback
        print('[ERROR] Exception in update_tracking_status:')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/donor_dashboard')
def donor_dashboard():
    from flask import session
    print('[DEBUG] Session at donor_dashboard:', dict(session))
    """
    Render donor dashboard showing Available NGOs, Requested NGOs, Accepted NGOs from auth.db.
    Also fetch and provide donor's food donations from SQLite database.
    NGOs are sorted by distance (nearest first) using donor's location.
    """
    import pprint
    # Get user info from database session if available
    db_session_id = session.get('db_session_id')
    print('[DEBUG] donor_dashboard session:', dict(session))
    
    # Get donor's location from session or database
    donor_lat = session.get('user_lat')
    donor_lon = session.get('user_lon')
    current_donor_id = session.get('user_id')
    
    if db_session_id:
        db_user = get_user_from_session(db_session_id)
        print('[DEBUG] donor_dashboard db_user:', db_user)
        if db_user:
            update_session_activity(db_session_id)
            user_info = db_user
            current_donor_name = db_user.get('user_name', None)
        else:
            # Fallback to Flask session
            user_info = {
                'user_name': session.get('user_name', 'Food Donor'),
                'user_email': session.get('user_email', ''),
                'user_role': session.get('user_role', 'food_donor'),
                'user_registration': session.get('user_registration', ''),
                'user_verified': session.get('user_verified', False)
            }
            current_donor_name = session.get('user_name', None)
    else:
        # Fallback to Flask session
        user_info = {
            'user_name': session.get('user_name', 'Food Donor'),
            'user_email': session.get('user_email', ''),
            'user_role': session.get('user_role', 'food_donor'),
            'user_registration': session.get('user_registration', ''),
            'user_verified': session.get('user_verified', False)
        }
        current_donor_name = session.get('user_name', None)
    
    # If donor location not in session, try to get from database
    if (donor_lat is None or donor_lon is None) and current_donor_id:
        app_conn = get_db_connection()
        donor_record = app_conn.execute('SELECT lat, lon FROM food_donors WHERE id = ?', (current_donor_id,)).fetchone()
        app_conn.close()
        if donor_record:
            donor_lat = donor_record['lat']
            donor_lon = donor_record['lon']
    
    print('[DEBUG] donor_dashboard user_info:', user_info)
    print('[DEBUG] donor_dashboard current_donor_name:', current_donor_name)
    print(f'[DEBUG] donor_dashboard donor location: lat={donor_lat}, lon={donor_lon}')
    
    auth_conn = get_auth_db_connection()
    app_conn = get_db_connection()

    # Get all NGOs from app.db (ngos table) with location info
    all_ngos = app_conn.execute('''
        SELECT id, name, email, address, lat, lon, verified
        FROM ngos
        ORDER BY name
    ''').fetchall()
    
    # Also get NGOs from auth.db (users table) for those registered via auth
    auth_ngos = auth_conn.execute('''
        SELECT id, name, email, registration_number, verified
        FROM users
        ORDER BY name
    ''').fetchall()

    # Convert to list of dicts and calculate distance
    available_ngos = []
    existing_names = set()  # Track by name to avoid duplicates
    existing_emails = set()  # Track by email to avoid duplicates
    
    for ngo in all_ngos:
        ngo_dict = dict(ngo)
        ngo_lat = ngo_dict.get('lat')
        ngo_lon = ngo_dict.get('lon')
        distance = calculate_distance(donor_lat, donor_lon, ngo_lat, ngo_lon)
        ngo_dict['distance'] = round(distance, 2) if distance != float('inf') else None
        ngo_dict['source'] = 'app'  # Mark source
        available_ngos.append(ngo_dict)
        if ngo_dict.get('name'):
            existing_names.add(ngo_dict['name'].lower())
        if ngo_dict.get('email'):
            existing_emails.add(ngo_dict['email'].lower())
    
    # Add auth NGOs if not already in the list (by name or email)
    for ngo in auth_ngos:
        ngo_dict = dict(ngo)
        ngo_name = (ngo_dict.get('name') or '').lower()
        ngo_email = (ngo_dict.get('email') or '').lower()
        # Skip if name or email already exists
        if ngo_name and ngo_name in existing_names:
            continue
        if ngo_email and ngo_email in existing_emails:
            continue
        ngo_dict['distance'] = None  # No location for auth NGOs
        ngo_dict['source'] = 'auth'  # Mark source
        available_ngos.append(ngo_dict)
        if ngo_name:
            existing_names.add(ngo_name)
        if ngo_email:
            existing_emails.add(ngo_email)
    
    # Sort NGOs by distance (nearest first, None values at the end)
    available_ngos.sort(key=lambda x: (x.get('distance') is None, x.get('distance') or float('inf')))
    
    # Get requested and accepted NGOs from assignment database
    from database.assignment_db import get_assignment_db_connection
    assign_conn = get_assignment_db_connection()
    
    requested_ngos = []
    accepted_ngos = []
    requested_ngo_names = set()  # Track by name for filtering
    accepted_ngo_names = set()
    
    if current_donor_id:
        # Get requests made by this donor
        requests = assign_conn.execute('''
            SELECT DISTINCT fdr.ngo_id, fdr.ngo_name, fdr.status, fdr.ngo_acceptance_status,
                   na.assigned_at, na.acceptance_time
            FROM food_donor_requests fdr
            JOIN ngo_assignments na ON fdr.assignment_id = na.id
            WHERE fdr.food_donor_id = ?
            ORDER BY fdr.request_time DESC
        ''', (current_donor_id,)).fetchall()
        
        requested_ngo_ids = set()
        accepted_ngo_ids = set()
        
        for req in requests:
            req_dict = dict(req)
            ngo_name = req_dict.get('ngo_name', '').lower() if req_dict.get('ngo_name') else ''
            
            if req_dict.get('ngo_acceptance_status') == 'accepted' or req_dict.get('status') == 'accepted':
                accepted_ngo_ids.add(req_dict['ngo_id'])
                if ngo_name:
                    accepted_ngo_names.add(ngo_name)
                # Find full NGO info by ID or name
                for ngo in available_ngos:
                    ngo_match = ngo['id'] == req_dict['ngo_id'] or (ngo.get('name', '').lower() == ngo_name and ngo_name)
                    if ngo_match:
                        ngo_copy = ngo.copy()
                        ngo_copy['acceptance_time'] = req_dict.get('acceptance_time')
                        accepted_ngos.append(ngo_copy)
                        break
            else:
                requested_ngo_ids.add(req_dict['ngo_id'])
                if ngo_name:
                    requested_ngo_names.add(ngo_name)
                for ngo in available_ngos:
                    ngo_match = ngo['id'] == req_dict['ngo_id'] or (ngo.get('name', '').lower() == ngo_name and ngo_name)
                    if ngo_match:
                        ngo_copy = ngo.copy()
                        ngo_copy['requested_at'] = req_dict.get('assigned_at')
                        requested_ngos.append(ngo_copy)
                        break
        
        # Remove requested and accepted NGOs from available list (by ID or name)
        available_ngos = [ngo for ngo in available_ngos 
                         if ngo['id'] not in requested_ngo_ids and ngo['id'] not in accepted_ngo_ids
                         and (ngo.get('name', '').lower() not in requested_ngo_names)
                         and (ngo.get('name', '').lower() not in accepted_ngo_names)]
    
    assign_conn.close()

    # Fetch food donations submitted by current donor from food_donors table
    if current_donor_name:
        donor_food_donations = app_conn.execute('''
            SELECT id, organization_name, food_type, quantity, ready_for_pickup_time, pickup_location,
                   category, cuisine_type, spice_level, created_at
            FROM food_donors
            WHERE organization_name = ?
            ORDER BY created_at DESC
        ''', (current_donor_name,)).fetchall()
        donor_food_donations = [dict(row) for row in donor_food_donations]
    else:
        donor_food_donations = []

    auth_conn.close()
    app_conn.close()

    return render_template('Donor_dashboard.html', 
                         available_ngos=available_ngos, 
                         requested_ngos=requested_ngos, 
                         accepted_ngos=accepted_ngos,
                         donor_food_donations=donor_food_donations,
                         donor_lat=donor_lat,
                         donor_lon=donor_lon,
                         **user_info)


@dashboard_bp.route('/ngo_dashboard')
def ngo_dashboard():
    """
    Render NGO dashboard showing Available and Accepted Food Donations from food_donors table.
    Food donors are sorted by distance (nearest first) using NGO's location.
    """
    # Get user info from database session if available
    db_session_id = session.get('db_session_id')
    auth_ngo_id = session.get('user_id')  # This is from auth.db
    app_ngo_id = session.get('app_ngo_id')  # This is from app.db (if stored during login)
    ngo_name = session.get('user_name', '')
    ngo_email = session.get('user_email', '')
    
    if db_session_id:
        db_user = get_user_from_session(db_session_id)
        if db_user:
            update_session_activity(db_session_id)
            user_info = db_user
            if not ngo_name:
                ngo_name = db_user.get('user_name', '')
            if not ngo_email:
                ngo_email = db_user.get('user_email', '')
        else:
            # Fallback to Flask session
            user_info = {
                'user_name': ngo_name,
                'user_email': ngo_email,
                'user_role': session.get('user_role', 'NGO'),
                'user_registration': session.get('user_registration', ''),
                'user_verified': session.get('user_verified', False),
                'user_id': auth_ngo_id
            }
    else:
        # Fallback to Flask session
        user_info = {
            'user_name': ngo_name,
            'user_email': ngo_email,
            'user_role': session.get('user_role', 'NGO'),
            'user_registration': session.get('user_registration', ''),
            'user_verified': session.get('user_verified', False),
            'user_id': auth_ngo_id
        }
    
    # CRITICAL FIX: Look up NGO in app.db by name or email to get correct ngo_id
    # The auth.db ID doesn't match app.db ID, so we need to find the NGO by name/email
    app_conn = get_db_connection()
    ngo_id = app_ngo_id  # Use stored app_ngo_id if available
    ngo_lat = None
    ngo_lon = None
    
    # If app_ngo_id is set, use it directly
    if ngo_id:
        ngo_record = app_conn.execute('SELECT lat, lon FROM ngos WHERE id = ?', (ngo_id,)).fetchone()
        if ngo_record:
            ngo_lat = ngo_record['lat']
            ngo_lon = ngo_record['lon']
    else:
        # Try to find NGO by name first, then by email
        if ngo_name:
            ngo_record = app_conn.execute('SELECT id, lat, lon FROM ngos WHERE name = ?', (ngo_name,)).fetchone()
            if ngo_record:
                ngo_id = ngo_record['id']
                ngo_lat = ngo_record['lat']
                ngo_lon = ngo_record['lon']
        
        if not ngo_id and ngo_email:
            ngo_record = app_conn.execute('SELECT id, lat, lon FROM ngos WHERE email = ?', (ngo_email,)).fetchone()
            if ngo_record:
                ngo_id = ngo_record['id']
                ngo_lat = ngo_record['lat']
                ngo_lon = ngo_record['lon']
        
        # If still no match, try auth.db ID as fallback
        if not ngo_id and auth_ngo_id:
            ngo_record = app_conn.execute('SELECT id, lat, lon FROM ngos WHERE id = ?', (auth_ngo_id,)).fetchone()
            if ngo_record:
                ngo_id = ngo_record['id']
                ngo_lat = ngo_record['lat']
                ngo_lon = ngo_record['lon']
    
    app_conn.close()
    
    print(f'[DEBUG] NGO Dashboard - auth_ngo_id: {auth_ngo_id}, app_ngo_id: {app_ngo_id}, resolved ngo_id: {ngo_id}, name: {ngo_name}, email: {ngo_email}')
    
    from database.assignment_db import get_assignment_db_connection
    conn = get_assignment_db_connection()
    app_conn = get_db_connection()

    # Show all food donors assigned to this NGO from both tables
    available_donations = conn.execute('''
        SELECT a.id as assignment_id, r.id as request_id, a.food_donor_id, a.food_donor_name, a.ngo_id, a.ngo_name, 
               r.status, r.ngo_acceptance_status, a.assigned_at
        FROM ngo_assignments a
        LEFT JOIN food_donor_requests r ON a.id = r.assignment_id
        WHERE a.ngo_id = ? AND (r.status IS NULL OR r.status = 'pending')
        ORDER BY a.assigned_at DESC
    ''', (ngo_id,)).fetchall() if ngo_id else []
    
    # Enrich donations with donor location and calculate distance
    available_donations_dict = []
    for donation in available_donations:
        d = dict(donation)
        # Use request_id for actions, fall back to assignment_id
        d['id'] = d.get('request_id') or d.get('assignment_id')
        donor_id = d.get('food_donor_id')
        if donor_id:
            donor_record = app_conn.execute('SELECT lat, lon, address, phone FROM food_donors WHERE id = ?', (donor_id,)).fetchone()
            if donor_record:
                d['donor_lat'] = donor_record['lat']
                d['donor_lon'] = donor_record['lon']
                d['donor_address'] = donor_record['address']
                d['donor_phone'] = donor_record['phone']
                distance = calculate_distance(ngo_lat, ngo_lon, donor_record['lat'], donor_record['lon'])
                d['distance'] = round(distance, 2) if distance != float('inf') else None
            else:
                d['distance'] = None
        else:
            d['distance'] = None
        available_donations_dict.append(d)
    
    # Sort by distance (nearest first)
    available_donations_dict.sort(key=lambda x: (x.get('distance') is None, x.get('distance') or float('inf')))

    accepted_donations = conn.execute('''
        SELECT a.id as assignment_id, r.id as request_id, a.food_donor_id, a.food_donor_name, a.ngo_id, a.ngo_name, 
               r.status, r.ngo_acceptance_status, a.acceptance_time, r.volunteer_id, r.volunteer_name
        FROM ngo_assignments a
        LEFT JOIN food_donor_requests r ON a.id = r.assignment_id
        WHERE a.ngo_id = ? AND r.status = 'accepted'
        ORDER BY a.acceptance_time DESC
    ''', (ngo_id,)).fetchall() if ngo_id else []
    
    # Enrich accepted donations with donor location and calculate distance
    accepted_donations_dict = []
    for donation in accepted_donations:
        d = dict(donation)
        # Use request_id for mark completed, fall back to assignment_id
        d['id'] = d.get('request_id') or d.get('assignment_id')
        donor_id = d.get('food_donor_id')
        if donor_id:
            donor_record = app_conn.execute('SELECT lat, lon, address, phone FROM food_donors WHERE id = ?', (donor_id,)).fetchone()
            if donor_record:
                d['donor_lat'] = donor_record['lat']
                d['donor_lon'] = donor_record['lon']
                d['donor_address'] = donor_record['address']
                d['donor_phone'] = donor_record['phone']
                distance = calculate_distance(ngo_lat, ngo_lon, donor_record['lat'], donor_record['lon'])
                d['distance'] = round(distance, 2) if distance != float('inf') else None
        accepted_donations_dict.append(d)

    conn.close()
    app_conn.close()

    return render_template('NGO_dashboard.html', 
                         available_donations=available_donations_dict, 
                         accepted_donations=accepted_donations_dict,
                         ngo_lat=ngo_lat,
                         ngo_lon=ngo_lon,
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
    app_conn = get_db_connection()

    # Get food donor requests categorized by status
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

    # Get all volunteers from app.db
    volunteers = app_conn.execute('''
        SELECT * FROM volunteers ORDER BY name
    ''').fetchall()

    # Get all food donors (from food_donor_requests table in assignment.db)
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
    donors_list = [dict(don) for don in donors]
    complaints_list = [dict(comp) for comp in complaints]

    # Fetch assignment data for the logged-in user from assignment.db
    user_email = session.get('user_email')
    user_role = session.get('user_role') or session.get('user_type')
    user_id = session.get('user_id')
    user_assignments = []
    if user_email:
        try:
            from database.get_user_assignments import get_user_assignments
            user_assignments = get_user_assignments(user_email)
        except Exception as e:
            user_assignments = []
    
    # Filter requests based on user role
    if user_role == 'food_donor' and user_id:
        # For donors, show only their requests
        assigned_requests_list = [r for r in assigned_requests_list if r.get('food_donor_id') == user_id]
        collected_requests_list = [r for r in collected_requests_list if r.get('food_donor_id') == user_id]
        in_transit_requests_list = [r for r in in_transit_requests_list if r.get('food_donor_id') == user_id]
        delivered_requests_list = [r for r in delivered_requests_list if r.get('food_donor_id') == user_id]
    elif user_role == 'NGO' and user_id:
        # For NGOs, show only requests to their NGO
        assigned_requests_list = [r for r in assigned_requests_list if r.get('ngo_id') == user_id]
        collected_requests_list = [r for r in collected_requests_list if r.get('ngo_id') == user_id]
        in_transit_requests_list = [r for r in in_transit_requests_list if r.get('ngo_id') == user_id]
        delivered_requests_list = [r for r in delivered_requests_list if r.get('ngo_id') == user_id]
    
    return render_template('progress.html', 
                           assigned_requests=assigned_requests_list,
                           collected_requests=collected_requests_list,
                           in_transit_requests=in_transit_requests_list,
                           delivered_requests=delivered_requests_list,
                           ngos=ngos_list,
                           volunteers=volunteers_list,
                           donors=donors_list,
                           complaints=complaints_list,
                           user_contact=session.get('user_contact'),
                           user_role=user_role,
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

    return render_template('volunteers/volunteer_dashboard.html',
                         assigned_requests=assigned_requests_dict,
                         completed_deliveries=completed_deliveries_dict,
                         **user_info)

