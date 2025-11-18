"""
Admin routes for NGO verification and system management
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from db import get_db_connection

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
def admin():
    """
    Admin dashboard - displays all NGOs for verification and system overview.
    """
    conn = get_db_connection()

    # Fetch all NGOs, ordered by verification status (pending first)
    ngos = conn.execute(
        'SELECT * FROM ngos ORDER BY verified ASC, id DESC'
    ).fetchall()

    # Get system statistics
    stats = conn.execute('''
        SELECT
            (SELECT COUNT(*) FROM ngos WHERE verified = 1) as verified_ngos,
            (SELECT COUNT(*) FROM ngos WHERE verified = 0) as pending_ngos,
            (SELECT COUNT(*) FROM volunteers) as total_volunteers,
            (SELECT COUNT(*) FROM food_requests WHERE status IN ('assigned', 'collected', 'in_transit')) as active_requests,
            (SELECT COUNT(*) FROM complaints WHERE status = 'pending') as pending_complaints
    ''').fetchone()

    # Get volunteers with assignments
    volunteers = conn.execute('''
        SELECT v.*, COUNT(fr.id) as active_assignments
        FROM volunteers v
        LEFT JOIN food_requests fr ON v.id = fr.assigned_volunteer_id
        AND fr.status IN ('assigned', 'collected', 'in_transit')
        GROUP BY v.id
        ORDER BY v.name
    ''').fetchall()

    # Get food donors
    donors = conn.execute('''
        SELECT DISTINCT donor_name, COUNT(*) as total_donations,
               COUNT(CASE WHEN status IN ('assigned', 'collected', 'in_transit') THEN 1 END) as active_donations
        FROM food_requests
        GROUP BY donor_name
        ORDER BY donor_name
    ''').fetchall()

    # Get complaints
    complaints = conn.execute('''
        SELECT c.*, n.name as ngo_name, v.name as volunteer_name
        FROM complaints c
        LEFT JOIN ngos n ON c.reporter_type = 'ngo' AND c.reporter_id = n.id
        LEFT JOIN volunteers v ON c.reporter_type = 'volunteer' AND c.reporter_id = v.id
        ORDER BY c.created_at DESC
    ''').fetchall()

    conn.close()

    return render_template('admin.html', ngos=ngos, stats=stats,
                         volunteers=volunteers, donors=donors, complaints=complaints)


@admin_bp.route('/verify_ngo/<int:id>', methods=['POST'])
def verify_ngo(id):
    """
    Verify an NGO by setting verified = 1 in the database.
    """
    conn = get_db_connection()
    conn.execute(
        'UPDATE ngos SET verified = 1 WHERE id = ?',
        (id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin.admin'))


@admin_bp.route('/reject_ngo/<int:id>', methods=['POST'])
def reject_ngo(id):
    """
    Reject an NGO by deleting it from the database.
    """
    conn = get_db_connection()
    conn.execute('DELETE FROM ngos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin.admin'))


@admin_bp.route('/resolve_complaint/<int:id>', methods=['POST'])
def resolve_complaint(id):
    """
    Resolve a complaint by updating its status and adding admin response.
    """
    response = request.form.get('admin_response', '')

    conn = get_db_connection()
    conn.execute('''
        UPDATE complaints
        SET status = 'resolved', admin_response = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (response, id))
    conn.commit()
    conn.close()

    return redirect(url_for('admin.admin'))


@admin_bp.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    """
    Allow NGOs, volunteers, or donors to submit complaints.
    """
    try:
        data = request.get_json()

        reporter_type = data.get('reporter_type')  # 'ngo', 'volunteer', 'donor'
        reporter_id = data.get('reporter_id')
        complaint_type = data.get('complaint_type')
        description = data.get('description')

        if not all([reporter_type, reporter_id, complaint_type, description]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO complaints (reporter_type, reporter_id, complaint_type, description)
            VALUES (?, ?, ?, ?)
        ''', (reporter_type, reporter_id, complaint_type, description))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Complaint submitted successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

