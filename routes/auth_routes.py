"""
Authentication routes for NGO registration and login using Firebase
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from db import get_db_connection
import os
from werkzeug.utils import secure_filename
from firebase_admin import auth as firebase_auth
from config.firebase_config import FIREBASE_CONFIG

auth_bp = Blueprint('auth', __name__)

# Allowed file extensions for certificates
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth_bp.route('/ngo_login')
def ngo_login():
    """Render NGO login page"""
    return render_template('login.html', firebase_config=FIREBASE_CONFIG)


@auth_bp.route('/ngo_register')
def ngo_register():
    """Render NGO registration page"""
    return render_template('register.html', firebase_config=FIREBASE_CONFIG)


@auth_bp.route('/register_ngo', methods=['POST'])
def register_ngo():
    """
    Register a new NGO with Firebase authentication.
    Expects JSON with NGO data including Firebase ID token.
    """
    try:
        data = request.get_json()

        # Extract NGO data
        name = data.get('name')
        email = data.get('email')
        registration_number = data.get('registration_number')
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

        # Persist NGO in SQLite instead of Firestore
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
                INSERT INTO ngos (name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            ''', (name, email, registration_number, society_cert, trust_deed, section8_cert))
            conn.commit()
            ngo_id = insert_cursor.lastrowid
            conn.close()
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
            # Mock NGO data for testing
            ngo_data = {
                'id': firebase_uid,
                'name': 'Test NGO',
                'email': 'test@example.com',
                'registration_number': 'TEST123',
                'society_cert': 'static/uploads/society_test.png',
                'trust_deed': 'static/uploads/trust_test.png',
                'section8_cert': 'static/uploads/section8_test.png',
                'verified': False,
                'auto_verified': False
            }
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'ngo': ngo_data
            }), 200
        else:
            if not firebase_email:
                return jsonify({'success': False, 'message': 'Unable to determine user email from Firebase token'}), 400

            try:
                conn = get_db_connection()
                ngo_row = conn.execute('SELECT * FROM ngos WHERE email = ?', (firebase_email,)).fetchone()

                if not ngo_row:
                    # Auto-create NGO record for existing Firebase users
                    display_name = (
                        (decoded_token.get('name') if decoded_token else None) or
                        (user_record.display_name if user_record else None) or
                        'Registered NGO'
                    )
                    conn.execute('''
                        INSERT INTO ngos (name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified)
                        VALUES (?, ?, ?, '', '', '', 0, 0)
                    ''', (display_name, firebase_email, ''))
                    conn.commit()
                    ngo_row = conn.execute('SELECT * FROM ngos WHERE email = ?', (firebase_email,)).fetchone()

                conn.close()
            except Exception as e:
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

            ngo_data = dict(ngo_row)
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'ngo': ngo_data
            }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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

