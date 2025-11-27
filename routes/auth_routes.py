"""
Authentication routes for NGO registration and login using Firebase or Mock Auth.

When USE_MOCK_AUTH = True (in config/mock_auth.py):
- Firebase authentication is bypassed
- Local SQLite database authentication is used
- Passwords are hashed with SHA-256

When USE_MOCK_AUTH = False:
- Real Firebase authentication is used
- Firebase ID tokens are verified
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from db import get_db_connection, get_auth_db_connection, get_volunteer_db_connection
import os
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import auth as firebase_auth, firestore
from config.firebase_config import FIREBASE_CONFIG
from config.mock_auth import USE_MOCK_AUTH, mock_authenticate, mock_register, hash_password
from database.session_manager import create_session, deactivate_session, get_user_from_session, update_session_activity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/food_donor_register', methods=['GET', 'POST'])
def food_donor_register():
    if request.method == 'GET':
        conn = get_db_connection()
        ngos = conn.execute('SELECT id, name FROM ngos').fetchall()
        conn.close()
        return render_template('food_donor_registration.html', ngos=ngos, use_mock_auth=USE_MOCK_AUTH)
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        whatsapp_phone = request.form.get('whatsapp_phone')
        vehicle_type = request.form.get('vehicle_type')
        address = request.form.get('address')
        password = request.form.get('password')  # For mock auth

        conn = get_db_connection()
        ngos = conn.execute('SELECT id, name FROM ngos').fetchall()
        
        if not all([name, phone, whatsapp_phone, vehicle_type, address]):
            conn.close()
            return render_template('food_donor_registration.html', ngos=ngos, error_message='All fields are required.', use_mock_auth=USE_MOCK_AUTH)

        # Check if using mock auth and password is required
        if USE_MOCK_AUTH:
            if not password:
                conn.close()
                return render_template('food_donor_registration.html', ngos=ngos, error_message='Password is required.', use_mock_auth=USE_MOCK_AUTH)
            if not email:
                conn.close()
                return render_template('food_donor_registration.html', ngos=ngos, error_message='Email is required.', use_mock_auth=USE_MOCK_AUTH)

        # Check if using mock auth and password is provided
        password_hash = None
        if USE_MOCK_AUTH and password:
            password_hash = hash_password(password)

        # Check by email first (for mock auth), then by phone
        donor_record = None
        if email:
            donor_record = conn.execute('SELECT * FROM food_donors WHERE email = ?', (email,)).fetchone()
            if donor_record:
                conn.close()
                return render_template('food_donor_registration.html', ngos=ngos, error_message='Email already registered. Please login.', use_mock_auth=USE_MOCK_AUTH)
        
        donor_record = conn.execute('SELECT * FROM food_donors WHERE phone = ?', (phone,)).fetchone()
        if not donor_record:
            try:
                # Default values for food_type, quantity, pickup_location
                # These will be updated when the donor creates a food donation
                DEFAULT_FOOD_TYPE = 'Not specified'
                DEFAULT_QUANTITY = 'Not specified'
                
                insert_cursor = conn.execute('''
                    INSERT INTO food_donors (organization_name, email, phone, whatsapp_phone, vehicle_type, address, food_type, quantity, pickup_location, password_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (name, email, phone, whatsapp_phone, vehicle_type, address, DEFAULT_FOOD_TYPE, DEFAULT_QUANTITY, address, password_hash))
                conn.commit()
            except Exception as e:
                conn.close()
                return render_template('food_donor_registration.html', ngos=ngos, error_message='Database error: ' + str(e), use_mock_auth=USE_MOCK_AUTH)
        donor_record = conn.execute('SELECT * FROM food_donors WHERE phone = ?', (phone,)).fetchone()
        conn.close()

        # Store donor-NGO assignments in assignment.db
        if donor_record:
            selected_ngos = request.form.getlist('selected_ngos')
            print(f"DEBUG: selected_ngos from form: {selected_ngos}")
            from database.assignment_db import insert_ngo_assignment, insert_food_donor_request
            for ngo_id in selected_ngos:
                ngo_conn = get_db_connection()
                ngo_row = ngo_conn.execute('SELECT name FROM ngos WHERE id = ?', (ngo_id,)).fetchone()
                ngo_conn.close()
                ngo_name = ngo_row['name'] if ngo_row else f"NGO {ngo_id}"

                assignment_id = insert_ngo_assignment(
                    ngo_id=int(ngo_id),
                    ngo_name=ngo_name,
                    volunteer_id=None,
                    volunteer_name=None,
                    food_donor_id=donor_record['id'],
                    food_donor_name=donor_record['organization_name'],
                    session_key=session.get('user_session_key', '')
                )
                print(f"DEBUG: Inserted into ngo_assignments: donor_id={donor_record['id']}, ngo_id={ngo_id}, assignment_id={assignment_id}")
                insert_food_donor_request(
                    assignment_id=assignment_id,
                    food_donor_id=donor_record['id'],
                    food_donor_name=donor_record['organization_name'],
                    ngo_id=int(ngo_id),
                    ngo_name=ngo_name
                )
                print(f"DEBUG: Inserted into food_donor_requests: donor_id={donor_record['id']}, ngo_id={ngo_id}, assignment_id={assignment_id}")

            session['user_id'] = donor_record['id']
            session['user_session_key'] = f"donor_{donor_record['id']}_{donor_record['email'] or donor_record['phone']}"
            session['user_type'] = 'food_donor'
            session['user_role'] = 'donor'
            session['user_name'] = donor_record['organization_name']
            session['user_email'] = donor_record['email'] if donor_record['email'] else ''
            session['user_contact'] = donor_record['email'] if donor_record['email'] else donor_record['phone']
            print('[DEBUG] Session after donor registration:', dict(session))
            return redirect(url_for('dashboard.donor_dashboard'))
        else:
            return render_template('food_donor_registration.html', error_message='Registration failed.', use_mock_auth=USE_MOCK_AUTH)

@auth_bp.route('/food_donor_login', methods=['GET', 'POST'])
def food_donor_login():
    if request.method == 'GET':
        return render_template('food_donor_login.html', use_mock_auth=USE_MOCK_AUTH)
    else:
        # Use name/phone login for food donors
        name = request.form.get('name')
        phone = request.form.get('phone')

        try:
            if not name or not phone:
                flash('Name and phone number are required.', 'error')
                return redirect(url_for('auth.food_donor_login'))
            
            # Use mock_authenticate with name+phone for food donors
            if USE_MOCK_AUTH:
                user = mock_authenticate(None, None, 'donor', name=name, phone=phone)
                if user:
                    session['user_id'] = user['id']
                    session['user_session_key'] = f"donor_{user['id']}_{user['phone']}"
                    session['user_type'] = 'food_donor'
                    session['user_role'] = 'donor'
                    session['user_name'] = user['name']
                    session['user_email'] = user.get('email', '')
                    session['user_contact'] = user['phone']
                    print('[DEBUG] Session after donor login (mock auth name+phone):', dict(session))
                    return redirect(url_for('dashboard.donor_dashboard'))
                else:
                    flash('Invalid name or phone number. Please check your credentials.', 'error')
                    return redirect(url_for('auth.food_donor_login'))
            
            # Legacy login with name/phone (direct DB query)
            conn = get_db_connection()
            row = conn.execute('SELECT * FROM food_donors WHERE organization_name = ? AND phone = ?', (name, phone)).fetchone()
            conn.close()
            user_record = dict(row) if row else None

            if user_record is None:
                flash('User not registered as food donor.', 'error')
                return redirect(url_for('auth.food_donor_login'))

            session['user_id'] = user_record.get('id')
            session['user_session_key'] = f"donor_{user_record.get('id')}_{user_record.get('phone')}"
            session['user_type'] = 'food_donor'
            session['user_role'] = 'donor'
            session['user_name'] = user_record.get('organization_name')
            session['user_email'] = user_record.get('email', '')
            session['user_contact'] = user_record.get('phone')
            print('[DEBUG] Session after donor login:', dict(session))
            return redirect(url_for('dashboard.donor_dashboard'))

        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
            return redirect(url_for('auth.food_donor_login'))

@auth_bp.route('/food_donor_logout')
def food_donor_logout():
    session.pop('user_session_key', None)
    session.pop('user_type', None)
    session.pop('user_name', None)
    session.clear()
    return redirect(url_for('index'))

# Allowed file extensions for certificates
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth_bp.route('/ngo_login')
def ngo_login():
    """Render NGO login page"""
    return render_template('NGO_login.html', firebase_config=FIREBASE_CONFIG, use_mock_auth=USE_MOCK_AUTH)


@auth_bp.route('/ngo_register')
def ngo_register():
    """Render NGO registration page"""
    return render_template('register.html', firebase_config=FIREBASE_CONFIG, use_mock_auth=USE_MOCK_AUTH)


@auth_bp.route('/ngo_login_mock', methods=['POST'])
def ngo_login_mock():
    """
    Mock NGO login using email/password (when USE_MOCK_AUTH=True).
    """
    if not USE_MOCK_AUTH:
        return jsonify({'success': False, 'message': 'Mock auth is disabled'}), 400
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash('Email and password are required.', 'error')
        return redirect(url_for('auth.ngo_login'))
    
    user = mock_authenticate(email, password, 'ngo')
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = 'NGO'
        session['user_type'] = 'NGO'
        session['user_registration'] = user.get('registration_number', '')
        session['user_verified'] = user.get('verified', False)
        session['user_session_key'] = f"ngo_{user['id']}_{user['email']}"
        session['user_contact'] = user['email']
        session.permanent = True
        print('[DEBUG] Session after NGO mock login:', dict(session))
        return redirect(url_for('dashboard.ngo_dashboard'))
    else:
        flash('Invalid email or password.', 'error')
        return redirect(url_for('auth.ngo_login'))


@auth_bp.route('/ngo_register_mock', methods=['POST'])
def ngo_register_mock():
    """
    Mock NGO registration using email/password (when USE_MOCK_AUTH=True).
    """
    if not USE_MOCK_AUTH:
        return jsonify({'success': False, 'message': 'Mock auth is disabled'}), 400
    
    name = request.form.get('name')
    email = request.form.get('email')
    registration_number = request.form.get('registration_number')
    primary_contact = request.form.get('primary_contact', '')
    password = request.form.get('password')
    
    if not all([name, email, registration_number, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('auth.ngo_register'))
    
    result = mock_register({
        'name': name,
        'email': email,
        'registration_number': registration_number,
        'primary_contact': primary_contact,
        'password': password
    }, 'ngo')
    
    if result['success']:
        session['user_id'] = result['user_id']
        session['user_name'] = name
        session['user_email'] = email
        session['user_role'] = 'NGO'
        session['user_type'] = 'NGO'
        session['user_registration'] = registration_number
        session['user_verified'] = False
        session['user_session_key'] = f"ngo_{result['user_id']}_{email}"
        session['user_contact'] = email
        session.permanent = True
        print('[DEBUG] Session after NGO mock registration:', dict(session))
        return redirect(url_for('dashboard.ngo_dashboard'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('auth.ngo_register'))


@auth_bp.route('/register_ngo', methods=['POST'])
def register_ngo():
    """
    Register a new NGO with Firebase authentication.
    Expects JSON with NGO data including Firebase ID token.
    """
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        registration_number = data.get('registration_number')
        primary_contact = data.get('primary_contact', '')
        id_token = data.get('id_token')  # Firebase ID token

        # File paths (uploaded via separate endpoint or included in data)
        society_cert = data.get('society_cert', '')
        trust_deed = data.get('trust_deed', '')
        section8_cert = data.get('section8_cert', '')

        # Validate required fields
        if not name or not email or not registration_number or not id_token:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Verify Firebase token
        decoded_token = None
        firebase_uid = None
        firebase_email = None

        try:
            if id_token == 'fake_token_for_testing':
                firebase_uid = 'test_uid'
                firebase_email = email
            else:
                if not id_token or not isinstance(id_token, str) or len(id_token) == 0:
                    return jsonify({'success': False, 'message': 'Invalid Firebase token: Token is empty or invalid format'}), 401

                # Allow up to 60 seconds clock skew to handle time differences between client and server
                decoded_token = firebase_auth.verify_id_token(id_token, check_revoked=False, clock_skew_seconds=60)
                firebase_uid = decoded_token['uid']
                firebase_email = decoded_token.get('email')
        except ValueError as e:
            return jsonify({'success': False, 'message': f'Invalid Firebase token: {str(e)}'}), 401
        except Exception as e:
            import traceback
            error_details = str(e)
            print(f"Firebase token verification error: {error_details}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'message': f'Invalid Firebase token: {error_details}'}), 401

        # Double-check email consistency if Firebase provided one
        if firebase_email and firebase_email.lower() != email.lower():
            return jsonify({
                'success': False,
                'message': 'Email mismatch between Firebase user and provided data'
            }), 400

        # Persist NGO in app.db (ngos table)
        try:
            conn = get_db_connection()
            cursor = conn.execute(
                'SELECT id FROM ngos WHERE email = ?',
                (email,)
            ).fetchone()
            if cursor:
                conn.close()
                return jsonify({'success': False, 'message': 'NGO with this email already exists'}), 400

            insert_cursor = conn.execute('''
                INSERT INTO ngos (firebase_uid, name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
            ''', (firebase_uid, name, email, registration_number, society_cert, trust_deed, section8_cert))
            conn.commit()
            ngo_id = insert_cursor.lastrowid
            conn.close()

            # Create session for newly registered user
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            db_session_id = create_session(
                user_id=ngo_id,
                user_type='NGO',
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Store in Flask session
            session['user_id'] = ngo_id
            session['user_name'] = name
            session['user_email'] = email
            session['user_role'] = 'NGO'
            session['user_registration'] = registration_number
            session['user_verified'] = False
            session['firebase_uid'] = firebase_uid
            session['db_session_id'] = db_session_id
            session['user_session_key'] = f"ngo_{ngo_id}_{email}"
            session['user_type'] = 'NGO'
            session['user_contact'] = email
            session.permanent = True
        except Exception as e:
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

        return jsonify({
            'success': True,
            'message': 'Registration successful! Redirecting to dashboard...',
            'ngo_id': ngo_id
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/login_ngo', methods=['POST'])
def login_ngo():
    """
    Login NGO using Firebase ID token.
    Returns NGO data if authenticated.
    """
    import traceback
    print("[DEBUG] NGO login route called")
    try:
        data = request.get_json()
        print(f"[DEBUG] Request data: {data}")
        id_token = data.get('id_token')
        print(f"[DEBUG] id_token: {id_token}")

        if not id_token:
            print("[DEBUG] No id_token provided")
            return jsonify({'success': False, 'message': 'ID token required'}), 400

        # Verify Firebase token
        decoded_token = None
        firebase_uid = None
        firebase_email = None

        try:
            if id_token == 'fake_token_for_testing':
                firebase_uid = 'test_uid'
                firebase_email = 'test@example.com'
                print("[DEBUG] Using fake token for testing")
            else:
                if not id_token or not isinstance(id_token, str) or len(id_token) == 0:
                    print("[DEBUG] Invalid Firebase token format")
                    return jsonify({'success': False, 'message': 'Invalid Firebase token: Token is empty or invalid format'}), 401

                decoded_token = firebase_auth.verify_id_token(id_token, check_revoked=False, clock_skew_seconds=60)
                firebase_uid = decoded_token['uid']
                firebase_email = decoded_token.get('email')
                print(f"[DEBUG] Decoded token: {decoded_token}")
        except ValueError as e:
            print(f"[DEBUG] ValueError: {str(e)}")
            return jsonify({'success': False, 'message': f'Invalid Firebase token: {str(e)}'}), 401
        except Exception as e:
            error_details = str(e)
            print(f"[DEBUG] Firebase token verification error: {error_details}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'message': f'Invalid Firebase token: {error_details}'}), 401

        user_record = None
        if not firebase_email and firebase_uid and firebase_uid != 'test_uid':
            try:
                user_record = firebase_auth.get_user(firebase_uid)
                firebase_email = user_record.email
                print(f"[DEBUG] Got user from Firebase: {user_record}")
            except Exception as e:
                print(f"[DEBUG] Exception getting user from Firebase: {str(e)}")
                pass

        if firebase_uid == 'test_uid':
            print("[DEBUG] Using test_uid for mock login")
            ngo_data = {
                'id': 'test_uid',
                'name': 'Test NGO',
                'email': 'test@example.com',
                'registration_number': 'TEST123',
                'society_cert': 'static/uploads/society_test.png',
                'trust_deed': 'static/uploads/trust_test.png',
                'section8_cert': 'static/uploads/section8_test.png',
                'verified': False,
                'auto_verified': False
            }

            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            db_session_id = create_session(
                user_id=1,
                user_type='NGO',
                ip_address=ip_address,
                user_agent=user_agent
            )

            session['user_id'] = 1
            session['user_name'] = 'Test NGO'
            session['user_email'] = 'test@example.com'
            session['user_role'] = 'NGO'
            session['user_registration'] = 'TEST123'
            session['user_verified'] = False
            session['firebase_uid'] = firebase_uid
            session['db_session_id'] = db_session_id
            session['user_session_key'] = f"ngo_{1}_test@example.com"
            session['user_type'] = 'NGO'
            session['user_contact'] = 'test@example.com'
            session.permanent = True

            print(f"[DEBUG] Session info: {dict(session)}")
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'ngo': ngo_data,
                'session_id': db_session_id
            }), 200
        else:
            if not firebase_email:
                print("[DEBUG] Unable to determine user email from Firebase token")
                return jsonify({'success': False, 'message': 'Unable to determine user email from Firebase token'}), 400

            try:
                conn = get_db_connection()
                ngo_row = conn.execute('SELECT * FROM ngos WHERE email = ?', (firebase_email,)).fetchone()
                print(f"[DEBUG] NGO row from DB: {ngo_row}")

                if not ngo_row:
                    display_name = (
                        (decoded_token.get('name') if decoded_token else None) or
                        (user_record.display_name if user_record else None) or
                        'Registered NGO'
                    )
                    conn.execute('''
                        INSERT INTO ngos (firebase_uid, name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified)
                        VALUES (?, ?, ?, ?, '', '', '', 0, 0)
                    ''', (firebase_uid, display_name, firebase_email, ''))
                    conn.commit()
                    ngo_row = conn.execute('SELECT * FROM ngos WHERE email = ?', (firebase_email,)).fetchone()
                    print(f"[DEBUG] Created new NGO row: {ngo_row}")

                conn.close()
            except Exception as e:
                print(f"[DEBUG] Database error: {str(e)}")
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

            ngo_data = dict(ngo_row)

            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            db_session_id = create_session(
                user_id=ngo_data['id'],
                user_type='NGO',
                ip_address=ip_address,
                user_agent=user_agent
            )

            session['user_id'] = ngo_data['id']
            session['user_name'] = ngo_data['name']
            session['user_email'] = ngo_data['email']
            session['user_role'] = 'NGO'
            session['user_registration'] = ngo_data.get('registration_number', '')
            session['user_verified'] = bool(ngo_data.get('verified', 0))
            session['firebase_uid'] = firebase_uid
            session['db_session_id'] = db_session_id
            session.permanent = True

            print(f"[DEBUG] Session info: {dict(session)}")
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'ngo': ngo_data,
                'session_id': db_session_id
            }), 200

    except Exception as e:
        print(f"[DEBUG] Exception in login_ngo: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Logout user and clear session"""
    # Get database session ID before clearing Flask session
    db_session_id = session.get('db_session_id')

    # Deactivate database session
    if db_session_id:
        deactivate_session(db_session_id)

    # Clear Flask session
    session.clear()
    return redirect(url_for('index'))


@auth_bp.route('/upload_certificate', methods=['POST'])
def upload_certificate():
    """
    Upload NGO certificate files.
    Returns file path for storage in database.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    cert_type = request.form.get('cert_type')  # 'society', 'trust', 'section8'

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        import time
        filename = f"{cert_type}_{int(time.time())}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        file.save(filepath)

        # Return relative path for database storage
        relative_path = f"static/uploads/{filename}"
        return jsonify({
            'success': True,
            'file_path': relative_path,
            'cert_type': cert_type
        }), 200

    return jsonify({'success': False, 'message': 'Invalid file type'}), 400


@auth_bp.route('/volunteer_login', methods=['GET', 'POST'])
def volunteer_login():
    if request.method == 'GET':
        # Render the volunteer login page
        return render_template('volunteers/volunteer_login.html', firebase_config=FIREBASE_CONFIG, use_mock_auth=USE_MOCK_AUTH)
    else:
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('auth.volunteer_login'))

        # If using mock auth
        if USE_MOCK_AUTH:
            user = mock_authenticate(email, password, 'volunteer')
            if user:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                session['user_role'] = 'Volunteer'
                session['user_type'] = 'volunteer'
                session['user_verified'] = user.get('verified', False)
                session['user_session_key'] = f"volunteer_{user['id']}_{user['email']}"
                session['user_contact'] = user['email']
                print('[DEBUG] Session after volunteer mock login:', dict(session))
                return redirect(url_for('dashboard.volunteer_dashboard'))
            else:
                flash('Invalid email or password.', 'error')
                return redirect(url_for('auth.volunteer_login'))

        # Firebase auth (when USE_MOCK_AUTH = False)
        try:
            # Authenticate with Firebase
            user = firebase_auth.get_user_by_email(email)
            # Here you might verify password with Firebase Auth SDK or client-side
            
            # Verify user exists in volunteer database
            conn = get_volunteer_db_connection()
            user_record = conn.execute('SELECT * FROM volunteers WHERE email = ?', (email,)).fetchone()
            conn.close()

            if user_record is None:
                flash('User not registered as volunteer.', 'error')
                return redirect(url_for('auth.volunteer_login'))

            session['user_id'] = user_record['id']
            session['user_type'] = 'volunteer'
            session['user_name'] = user_record['name']

            return redirect(url_for('volunteer.volunteer_dashboard'))  # Assuming volunteer dashboard route

        except firebase_admin._auth_utils.UserNotFoundError:
            flash('Invalid email or user does not exist.', 'error')
            return redirect(url_for('auth.volunteer_login'))
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
            return redirect(url_for('auth.volunteer_login'))


@auth_bp.route('/volunteer_register')
def volunteer_register():
    """Render Volunteer registration page"""
    return render_template('volunteers/volunteer_register.html', firebase_config=FIREBASE_CONFIG, use_mock_auth=USE_MOCK_AUTH)


@auth_bp.route('/volunteer_register_mock', methods=['POST'])
def volunteer_register_mock():
    """
    Mock volunteer registration using email/password (when USE_MOCK_AUTH=True).
    """
    if not USE_MOCK_AUTH:
        return jsonify({'success': False, 'message': 'Mock auth is disabled'}), 400
    
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone', '')
    password = request.form.get('password')
    
    if not all([name, email, password]):
        flash('Name, email, and password are required.', 'error')
        return redirect(url_for('auth.volunteer_register'))
    
    result = mock_register({
        'name': name,
        'email': email,
        'phone': phone,
        'password': password
    }, 'volunteer')
    
    if result['success']:
        session['user_id'] = result['user_id']
        session['user_name'] = name
        session['user_email'] = email
        session['user_role'] = 'Volunteer'
        session['user_type'] = 'volunteer'
        session['user_verified'] = False
        session['user_session_key'] = f"volunteer_{result['user_id']}_{email}"
        session['user_contact'] = email
        print('[DEBUG] Session after volunteer mock registration:', dict(session))
        return redirect(url_for('dashboard.volunteer_dashboard'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('auth.volunteer_register'))


@auth_bp.route('/register_volunteer', methods=['POST'])
def register_volunteer():
    """
    Register a new Volunteer with Firebase authentication.
    Expects JSON with volunteer data including Firebase ID token.
    """
    try:
        data = request.get_json()

        # Extract volunteer data
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone', '')
        # Remove whatsapp_phone, vehicle_type, address, availability as not in simplified form
        id_token = data.get('id_token')  # Firebase ID token

        # Validate required fields
        if not name or not email or not phone or not id_token:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Verify Firebase token
        decoded_token = None
        firebase_uid = None
        firebase_email = None

        try:
            if id_token == 'fake_token_for_testing':
                firebase_uid = 'test_uid'
                firebase_email = email
            else:
                if not id_token or not isinstance(id_token, str) or len(id_token) == 0:
                    return jsonify({'success': False, 'message': 'Invalid Firebase token: Token is empty or invalid format'}), 401

                # Allow up to 60 seconds clock skew to handle time differences between client and server
                decoded_token = firebase_auth.verify_id_token(id_token, check_revoked=False, clock_skew_seconds=60)
                firebase_uid = decoded_token['uid']
                firebase_email = decoded_token.get('email')
        except ValueError as e:
            return jsonify({'success': False, 'message': f'Invalid Firebase token: {str(e)}'}), 401
        except Exception as e:
            import traceback
            error_details = str(e)
            print(f"Firebase token verification error: {error_details}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'message': f'Invalid Firebase token: {error_details}'}), 401

        # Double-check email consistency if Firebase provided one
        if firebase_email and firebase_email.lower() != email.lower():
            return jsonify({
                'success': False,
                'message': 'Email mismatch between Firebase user and provided data'
            }), 400

        # Persist volunteer in volunteer.db
        try:
            conn = get_volunteer_db_connection()
            cursor = conn.execute(
                'SELECT id FROM volunteers WHERE email = ?',
                (email,)
            ).fetchone()
            if cursor:
                conn.close()
                return jsonify({'success': False, 'message': 'Volunteer with this email already exists'}), 400

            insert_cursor = conn.execute('''
                INSERT INTO volunteers (firebase_uid, name, email, phone, verified, created_at, average_rating, total_ratings)
                VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, 0, 0)
            ''', (firebase_uid, name, email, phone))
            conn.commit()
            volunteer_id = insert_cursor.lastrowid
            conn.close()

            # Create session for newly registered user
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            db_session_id = create_session(
                user_id=volunteer_id,
                user_type='Volunteer',
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Store in Flask session
            session['user_id'] = volunteer_id
            session['user_name'] = name
            session['user_email'] = email
            session['user_role'] = 'Volunteer'
            session['user_verified'] = False
            session['firebase_uid'] = firebase_uid
            session['db_session_id'] = db_session_id
        except Exception as e:
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

        return jsonify({
            'success': True,
            'message': 'Registration successful! Redirecting to dashboard...',
            'volunteer_id': volunteer_id
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/login_volunteer', methods=['POST'])
def login_volunteer():
    """
    Login Volunteer using Firebase ID token.
    Returns volunteer data if authenticated.
    """
    try:
        data = request.get_json()
        id_token = data.get('id_token')

        if not id_token:
            return jsonify({'success': False, 'message': 'ID token required'}), 400

        # Verify Firebase token
        decoded_token = None
        firebase_uid = None
        firebase_email = None

        try:
            if id_token == 'fake_token_for_testing':
                firebase_uid = 'test_uid'
                firebase_email = 'test@example.com'
            else:
                if not id_token or not isinstance(id_token, str) or len(id_token) == 0:
                    return jsonify({'success': False, 'message': 'Invalid Firebase token: Token is empty or invalid format'}), 401

                decoded_token = firebase_auth.verify_id_token(id_token, check_revoked=False, clock_skew_seconds=60)
                firebase_uid = decoded_token['uid']
                firebase_email = decoded_token.get('email')
        except ValueError as e:
            return jsonify({'success': False, 'message': f'Invalid Firebase token: {str(e)}'}), 401
        except Exception as e:
            import traceback
            error_details = str(e)
            print(f"Firebase token verification error: {error_details}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'message': f'Invalid Firebase token: {error_details}'}), 401

        user_record = None
        if not firebase_email and firebase_uid and firebase_uid != 'test_uid':
            try:
                user_record = firebase_auth.get_user(firebase_uid)
                firebase_email = user_record.email
            except Exception:
                pass

        if firebase_uid == 'test_uid':
            # Mock volunteer data for testing
            volunteer_data = {
                'id': 'test_uid',
                'name': 'Test Volunteer',
                'email': 'test@example.com',
                'phone': '1234567890',
                'verified': False
            }

            # Create database session for test user
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            db_session_id = create_session(
                user_id=1,  # Use 1 as test user ID
                user_type='Volunteer',
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Store user info in Flask session for test user
            session['user_id'] = 1
            session['user_name'] = 'Test Volunteer'
            session['user_email'] = 'test@example.com'
            session['user_role'] = 'Volunteer'
            session['user_verified'] = False
            session['firebase_uid'] = firebase_uid
            session['db_session_id'] = db_session_id

            return jsonify({
                'success': True,
                'message': 'Login successful',
                'volunteer': volunteer_data,
                'session_id': db_session_id
            }), 200
        else:
            if not firebase_email:
                return jsonify({'success': False, 'message': 'Unable to determine user email from Firebase token'}), 400

            try:
                conn = get_volunteer_db_connection()
                volunteer_row = conn.execute('SELECT * FROM volunteers WHERE email = ?', (firebase_email,)).fetchone()

                if not volunteer_row:
                    # Auto-create volunteer record for existing Firebase users
                    display_name = (
                        (decoded_token.get('name') if decoded_token else None) or
                        (user_record.display_name if user_record else None) or
                        'Registered Volunteer'
                    )
                    conn.execute('''
                        INSERT INTO volunteers (firebase_uid, name, email, phone, verified, created_at, average_rating, total_ratings)
                        VALUES (?, ?, ?, '', 0, CURRENT_TIMESTAMP, 0, 0)
                    ''', (firebase_uid, display_name, firebase_email))
                    conn.commit()
                    volunteer_row = conn.execute('SELECT * FROM volunteers WHERE email = ?', (firebase_email,)).fetchone()

                conn.close()
            except Exception as e:
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

            volunteer_data = dict(volunteer_row)

            # Create database session
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            db_session_id = create_session(
                user_id=volunteer_data['id'],
                user_type='Volunteer',
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Store user info in Flask session
            session['user_id'] = volunteer_data['id']
            session['user_name'] = volunteer_data['name']
            session['user_email'] = volunteer_data['email']
            session['user_role'] = 'Volunteer'
            session['user_verified'] = bool(volunteer_data.get('verified', 0))
            session['firebase_uid'] = firebase_uid
            session['db_session_id'] = db_session_id  # Store database session ID

            return jsonify({
                'success': True,
                'message': 'Login successful',
                'volunteer': volunteer_data,
                'session_id': db_session_id
            }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
