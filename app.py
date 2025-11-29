# Flask application for Surplus-to-NGO Connector
# Complete food redistribution system with volunteer management

from flask import Flask, render_template, send_from_directory, request, session
from flask_cors import CORS
import os
from routes.auth_routes import auth_bp
from routes.volunteer_routes import volunteer_bp
from routes.dashboard_routes import dashboard_bp
from routes.admin_routes import admin_bp
from routes.donor_routes import donor_bp
from routes.ngo_routes import ngo_bp


app = Flask(__name__, template_folder='Templates')
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Enable CORS for all routes
CORS(app)

# Context processor to inject session info into all templates
@app.context_processor
def inject_session_info():
    return dict(
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        user_email=session.get('user_email'),
        user_role=session.get('user_role') or session.get('user_type'),
        user_type=session.get('user_type'),
        user_phone=session.get('user_contact'),
        user_session_key=session.get('user_session_key'),
        db_session_id=session.get('db_session_id'),
        is_logged_in=bool(session.get('user_name') and (session.get('user_email') or session.get('user_contact')))
    )

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(volunteer_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(donor_bp)
app.register_blueprint(ngo_bp, url_prefix='/ngo')


@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')


@app.route('/food_donor')
def food_donor():
    """Render the food donor page"""
    from db import get_db_connection
    ngo_id = request.args.get('ngo_id', type=int)
    conn = get_db_connection()
    ngos = conn.execute('SELECT id, name FROM ngos WHERE verified = 1 ORDER BY name').fetchall()
    conn.close()
    return render_template('food_donor.html', ngos=ngos, selected_ngo_id=ngo_id)


@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/live_tracking')
def live_tracking():
    """Render the live tracking page"""
    return render_template('live_tracking.html')


@app.route('/init_db')
def init_db_route():
    """Manually initialize the database"""
    from db import init_db
    try:
        init_db()
        return "Database initialized successfully!"
    except Exception as e:
        return "Error initializing database: " + str(e)


@app.route('/test_ngo_login/<int:ngo_id>')
def test_ngo_login(ngo_id):
    """
    Test route to simulate NGO login for development/testing.
    Sets session variables to simulate being logged in as an NGO.
    """
    from db import get_db_connection
    conn = get_db_connection()
    ngo = conn.execute('SELECT id, name, email FROM ngos WHERE id = ?', (ngo_id,)).fetchone()
    conn.close()
    
    if not ngo:
        return f"NGO with ID {ngo_id} not found", 404
    
    # Set session variables
    session['user_id'] = ngo['id']
    session['app_ngo_id'] = ngo['id']
    session['user_name'] = ngo['name']
    session['user_email'] = ngo['email']
    session['user_role'] = 'NGO'
    session['user_type'] = 'NGO'
    session['user_contact'] = ngo['email']
    session['user_session_key'] = f"ngo_{ngo['id']}_{ngo['email']}"
    session.permanent = True
    
    return f"Logged in as NGO: {ngo['name']} (ID: {ngo['id']}). <a href='/ngo_dashboard'>Go to NGO Dashboard</a>"

if __name__ == '__main__':
    # Initialize all databases on startup
    from db import init_all_databases
    print("Initializing databases...")
    init_all_databases()
    print("Databases initialized successfully!")
    app.run(debug=True, host='0.0.0.0', port=5001)
