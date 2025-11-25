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
        from database.assignment_db import accept_food_donation_request
        accept_food_donation_request(request_id)
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
    print('[DEBUG] donor_dashboard user_info:', user_info)
    print('[DEBUG] donor_dashboard current_donor_name:', current_donor_name)
    
    auth_conn = get_auth_db_connection()
    app_conn = get_db_connection()

    # Get all users from auth.db
    all_ngos = auth_conn.execute('''
        SELECT id, name, email, registration_number, verified
        FROM users
        ORDER BY name
    ''').fetchall()

    # For now, show all NGOs from auth.db as available
    # TODO: Implement proper categorization based on food_requests status
    available_ngos = [dict(ngo) for ngo in all_ngos]
    requested_ngos = []
    accepted_ngos = []

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
                         **user_info)


@dashboard_bp.route('/ngo_dashboard')
def ngo_dashboard():
    """
    Render NGO dashboard showing Available and Accepted Food Donations from food_donors table.
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
    
    from database.assignment_db import get_assignment_db_connection
    conn = get_assignment_db_connection()

    ngo_id = user_info.get('user_id')
    # Show all food donors assigned to this NGO from both tables
    available_donations = conn.execute('''
        SELECT a.id, a.food_donor_id, a.food_donor_name, a.ngo_id, a.ngo_name, r.status, r.ngo_acceptance_status, a.assigned_at
        FROM ngo_assignments a
        LEFT JOIN food_donor_requests r ON a.id = r.assignment_id
        WHERE a.ngo_id = ? AND (r.status IS NULL OR r.status = 'pending')
        ORDER BY a.assigned_at DESC
    ''', (ngo_id,)).fetchall() if ngo_id else []
    available_donations_dict = [dict(row) for row in available_donations]

    accepted_donations = conn.execute('''
        SELECT a.id, a.food_donor_id, a.food_donor_name, a.ngo_id, a.ngo_name, r.status, r.ngo_acceptance_status, a.acceptance_time
        FROM ngo_assignments a
        LEFT JOIN food_donor_requests r ON a.id = r.assignment_id
        WHERE a.ngo_id = ? AND r.status = 'accepted'
        ORDER BY a.acceptance_time DESC
    ''', (ngo_id,)).fetchall() if ngo_id else []
    accepted_donations_dict = [dict(row) for row in accepted_donations]

    conn.close()

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
        SELECT * FROM food_donor_requests WHERE status = 'accepted' AND ngo_acceptance_status = 'accepted' ORDER BY id DESC
    """).fetchall()
    in_transit_requests = conn.execute("""
        SELECT * FROM food_donor_requests WHERE status = 'in_transit' ORDER BY id DESC
    """).fetchall()
    delivered_requests = conn.execute("""
        SELECT * FROM food_donor_requests WHERE status = 'delivered' ORDER BY id DESC
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

