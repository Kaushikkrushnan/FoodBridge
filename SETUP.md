# Flask Food Redistribution System - Setup Guide

## Project Structure

```
project/
├── app.py                         # Flask main app entry
├── db.py                          # SQLite connection helper
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── focus_timer.css
│   │   └── dashboard.css
│   └── uploads/                   # for uploaded NGO certificates
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── admin.html
│   ├── donor_dashboard.html
│   ├── ngo_dashboard.html
│   └── (other templates)
└── routes/
    ├── auth_routes.py
    ├── dashboard_routes.py
    ├── volunteer_routes.py
    └── admin_routes.py
```

## Installation

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Initialize database:
The database will be automatically created when you run the app for the first time.

## Firebase Setup (Required for NGO Authentication)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use an existing one
3. Enable Authentication → Email/Password
4. Get your Firebase configuration
5. Update Firebase config in `config/firebase_config.py` (or it will be passed via Flask templates):

```javascript
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_AUTH_DOMAIN",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
};
```

## Running the Application

```bash
python3 app.py
```

The app will run on `http://localhost:5000`

## Routes

- `/` - Home page
- `/donor` - Donor/Volunteer page
- `/ngo_login` - NGO login page
- `/ngo_register` - NGO registration page
- `/donor_dashboard` - Donor dashboard (shows verified NGOs)
- `/ngo_dashboard` - NGO dashboard (shows active food requests)
- `/admin` - Admin dashboard for NGO verification

## API Endpoints

### Volunteer Management
- `POST /register_volunteer` - Register a new volunteer
- `POST /update_volunteer_location` - Update volunteer location
- `GET /get_available_volunteers` - Get available volunteers near a location
- `POST /assign_nearest_volunteer` - Assign nearest volunteer to a request

### NGO Authentication
- `POST /register_ngo` - Register new NGO (after Firebase auth)
- `POST /upload_certificate` - Upload NGO certificate files

### Admin
- `POST /verify_ngo/<id>` - Verify an NGO
- `POST /reject_ngo/<id>` - Reject an NGO

## Database Schema

### ngos table
- id, name, email, registration_number
- society_cert, trust_deed, section8_cert (file paths)
- verified (0/1), auto_verified (0/1)

### volunteers table
- id, name, contact, lat, lon
- available_from, available_to (time slots)
- is_available (0/1), last_seen (timestamp)

### food_requests table
- id, donor_name, food_type, quantity
- pickup_location, pickup_lat, pickup_lon, pickup_time
- status, assigned_volunteer_id
- food_category, cuisine_type, spice_level

## Features

1. **NGO Registration & Login**
   - Firebase Authentication
   - Certificate upload (3 required documents)
   - Admin verification system

2. **Volunteer Management**
   - Registration with location
   - Real-time location updates
   - Automatic assignment based on distance (Haversine formula)
   - Time slot availability checking

3. **Dashboards**
   - Donor dashboard: View verified NGOs
   - NGO dashboard: View active food requests with filters
   - Admin dashboard: Verify/reject NGOs

4. **Food Request Matching**
   - Automatic volunteer assignment
   - Distance-based matching
   - Availability checking

## Notes

- All file uploads are stored in `static/uploads/`
- Database is SQLite at `database/app.db`
- Firebase config must be updated in `config/firebase_config.py` for authentication to work
- For production, change `SECRET_KEY` in `app.py`

