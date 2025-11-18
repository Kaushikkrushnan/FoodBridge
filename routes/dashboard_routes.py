"""
Dashboard routes for Donor and NGO dashboards
"""
from flask import Blueprint, render_template
from db import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/donor_dashboard')
def donor_dashboard():
    """
    Render donor dashboard showing verified NGOs and accepted food donors (NGOs that accepted donations).
    """
    conn = get_db_connection()

    # Get only verified NGOs with their current request status
    ngos = conn.execute('''
        SELECT n.*,
               CASE WHEN EXISTS(
                   SELECT 1 FROM food_requests fr
                   WHERE fr.ngo_id = n.id AND fr.status IN ('assigned', 'collected', 'in_transit')
               ) THEN 'occupied' ELSE 'vacant' END as status
        FROM ngos n WHERE n.verified = 1 ORDER BY n.name
    ''').fetchall()

    # Get accepted NGOs (NGOs that have accepted food donations)
    accepted_ngos = conn.execute('''
        SELECT DISTINCT n.*, COUNT(fr.id) as accepted_donations_count
        FROM ngos n
        JOIN food_requests fr ON n.id = fr.ngo_id
        WHERE fr.status IN ('assigned', 'collected', 'in_transit')
        GROUP BY n.id ORDER BY n.name
    ''').fetchall()

    conn.close()

    # Convert Row objects to dicts for JSON serialization
    ngos_dict = [dict(row) for row in ngos]
    accepted_ngos_dict = [dict(row) for row in accepted_ngos]

    return render_template('donor_dashboard.html', ngos=ngos_dict, accepted_ngos=accepted_ngos_dict)


@dashboard_bp.route('/ngo_dashboard')
def ngo_dashboard():
    """
    Render NGO dashboard showing active food requests and assigned food donors.
    """
    conn = get_db_connection()

    # Get active food requests with donor info
    active_requests = conn.execute('''
        SELECT fr.*, n.name as ngo_name, n.email as ngo_email
        FROM food_requests fr
        LEFT JOIN ngos n ON fr.ngo_id = n.id
        WHERE fr.status = 'active' ORDER BY fr.id DESC
    ''').fetchall()

    # Get assigned food requests (assigned to NGOs)
    assigned_requests = conn.execute('''
        SELECT fr.*, n.name as ngo_name, n.email as ngo_email, v.name as volunteer_name
        FROM food_requests fr
        LEFT JOIN ngos n ON fr.ngo_id = n.id
        LEFT JOIN volunteers v ON fr.assigned_volunteer_id = v.id
        WHERE fr.status IN ('assigned', 'collected', 'in_transit') ORDER BY fr.id DESC
    ''').fetchall()

    conn.close()

    # Convert Row objects to dicts for JSON serialization
    active_requests_dict = [dict(row) for row in active_requests]
    assigned_requests_dict = [dict(row) for row in assigned_requests]

    return render_template('ngo_dashboard.html', food_requests=active_requests_dict, assigned_requests=assigned_requests_dict)


@dashboard_bp.route('/progress')
def progress():
    """
    Render progress tracking page with live map for assigned food requests.
    """
    conn = get_db_connection()

    # Get assigned food requests with volunteer and NGO info
    requests = conn.execute('''
        SELECT
            fr.id,
            fr.donor_name,
            fr.food_type,
            fr.quantity,
            fr.pickup_location,
            fr.pickup_lat,
            fr.pickup_lon,
            fr.status,
            fr.ngo_id,
            v.name as volunteer_name,
            v.lat as volunteer_lat,
            v.lon as volunteer_lon,
            v.average_rating,
            v.total_ratings,
            n.name as ngo_name,
            n.lat as ngo_lat,
            n.lon as ngo_lon,
            n.address as ngo_address
        FROM food_requests fr
        LEFT JOIN volunteers v ON fr.assigned_volunteer_id = v.id
        LEFT JOIN ngos n ON fr.ngo_id = n.id
        WHERE fr.status IN ('assigned', 'collected', 'in_transit')
        ORDER BY fr.id DESC
    ''').fetchall()

    # Get unique NGOs involved in these requests
    ngo_ids = list(set(req['ngo_id'] for req in requests if req['ngo_id']))
    ngos = []
    if ngo_ids:
        placeholders = ','.join('?' * len(ngo_ids))
        ngos = conn.execute(f'''
            SELECT id, name, email, address, lat, lon
            FROM ngos
            WHERE id IN ({placeholders})
            ORDER BY name
        ''', ngo_ids).fetchall()

    # Get all volunteers for admin view
    volunteers = conn.execute('''
        SELECT v.*, COUNT(fr.id) as active_assignments
        FROM volunteers v
        LEFT JOIN food_requests fr ON v.id = fr.assigned_volunteer_id
        AND fr.status IN ('assigned', 'collected', 'in_transit')
        GROUP BY v.id
        ORDER BY v.name
    ''').fetchall()

    # Get all food donors (from food_requests table)
    donors = conn.execute('''
        SELECT DISTINCT donor_name, COUNT(*) as total_donations,
               COUNT(CASE WHEN status IN ('assigned', 'collected', 'in_transit') THEN 1 END) as active_donations
        FROM food_requests
        GROUP BY donor_name
        ORDER BY donor_name
    ''').fetchall()

    # Get complaints/issues (placeholder - can be expanded)
    complaints = conn.execute('''
        SELECT 'No complaints reported' as message, 0 as count
    ''').fetchall()

    conn.close()

    # Convert to list of dicts and add mock ETA
    requests_list = []
    for req in requests:
        req_dict = dict(req)
        # Mock ETA calculation based on status
        if req_dict['status'] == 'assigned':
            req_dict['eta_minutes'] = 15
        elif req_dict['status'] == 'collected':
            req_dict['eta_minutes'] = 0
        elif req_dict['status'] == 'in_transit':
            req_dict['eta_minutes'] = 8
        else:
            req_dict['eta_minutes'] = 0
        requests_list.append(req_dict)

    # Convert NGO rows to dicts
    ngos_list = [dict(ngo) for ngo in ngos]
    volunteers_list = [dict(vol) for vol in volunteers]
    donors_list = [dict(don) for don in donors]
    complaints_list = [dict(comp) for comp in complaints]

    return render_template('progress.html', requests=requests_list, ngos=ngos_list,
                         volunteers=volunteers_list, donors=donors_list, complaints=complaints_list)

