# Flask application for Surplus-to-NGO Connector
# Complete food redistribution system with volunteer management

from flask import Flask, render_template, send_from_directory
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

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(volunteer_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(donor_bp)
app.register_blueprint(ngo_bp)


@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')


@app.route('/food_donor')
def food_donor():
    """Render the food donor page"""
    return render_template('food_donor.html')


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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
