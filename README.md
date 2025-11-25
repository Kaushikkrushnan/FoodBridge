# FoodBridge - Surplus-to-NGO Connector

A platform that bridges surplus food providers and NGOs in real time, helping reduce food waste while feeding more people.

## Overview

FoodBridge connects three key stakeholders:
- **Food Donors**: Restaurants, bakeries, and organizations with surplus food
- **NGOs**: Non-profit organizations that distribute food to those in need
- **Volunteers**: Individuals who help with food pickup and delivery

## Features

### For Food Donors
- Register and submit food donations with details (type, quantity, pickup time/location)
- Select food specifications (vegetarian/non-vegetarian, cuisine type, spice level)
- View and accept NGO requests
- Track donation status

### For NGOs
- Register with Firebase authentication
- View available food donations
- Accept donations and coordinate pickup
- Rate volunteers after delivery

### For Volunteers
- Register and login via Firebase
- View assigned deliveries
- Update delivery status (collected, in-transit, delivered)
- Track location for live updates

### Live Tracking
- Real-time volunteer location tracking
- Progress monitoring for food donations
- Status updates throughout the delivery process

## Screenshots

### Homepage
![Homepage](https://github.com/user-attachments/assets/df1fd485-c128-46c2-96ce-b0169a0fea4d)

### Donor Dashboard
![Donor Dashboard](https://github.com/user-attachments/assets/38ffadd1-381f-4b61-a34a-1bfbe1597936)

### Food Donor Portal
![Food Donor Portal](https://github.com/user-attachments/assets/b8f9f618-0d44-46a8-8aae-1b3df8dc7ae0)

### NGO Dashboard
![NGO Dashboard](https://github.com/user-attachments/assets/4f503c6e-73db-4627-9dc3-714acece04a5)

## Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Kaushikkrushnan/FoodBridge.git
cd FoodBridge
```

2. Install dependencies:
```bash
pip install flask flask-cors firebase-admin
```

3. Start the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5001
```

## Project Structure

```
FoodBridge/
├── app.py                 # Main Flask application
├── db.py                  # Database connection utilities
├── config/
│   ├── firebase_config.py # Firebase configuration
│   └── firebase-service-account.json
├── database/
│   ├── app.db            # Main SQLite database
│   ├── auth.db           # Authentication database
│   ├── assignment.db     # Assignment tracking database
│   ├── volunteer.db      # Volunteer database
│   ├── assignment_db.py  # Assignment database utilities
│   └── session_manager.py # Session management
├── routes/
│   ├── auth_routes.py    # Authentication routes
│   ├── admin_routes.py   # Admin routes
│   ├── dashboard_routes.py # Dashboard routes
│   ├── donor_routes.py   # Donor routes
│   ├── ngo_routes.py     # NGO routes
│   └── volunteer_routes.py # Volunteer routes
├── Templates/
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── Donor_dashboard.html
│   ├── NGO_dashboard.html
│   ├── Food_donor.html
│   ├── register.html     # NGO registration
│   ├── NGO_login.html
│   ├── live_tracking.html
│   ├── progress.html
│   └── volunteers/
│       ├── volunteer_login.html
│       ├── volunteer_register.html
│       └── volunteer_dashboard.html
└── static/
    └── css/
        └── style.css
```

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Authentication**: Firebase Auth
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript
- **Maps**: Leaflet.js for live tracking

## Usage Flow

1. **Food Donor Flow**:
   - Register/Login as food donor
   - Submit food donation with details
   - Select NGO to donate to
   - Track donation status

2. **NGO Flow**:
   - Register/Login as NGO
   - View available food donations
   - Accept donations
   - Assign volunteers for pickup

3. **Volunteer Flow**:
   - Register/Login as volunteer
   - View assigned pickups
   - Update delivery status
   - Complete delivery

## API Endpoints

### Authentication
- `POST /register_ngo` - Register new NGO
- `POST /login_ngo` - Login NGO
- `POST /register_volunteer` - Register volunteer
- `POST /login_volunteer` - Login volunteer
- `POST /food_donor_register` - Register food donor
- `POST /food_donor_login` - Login food donor

### Dashboards
- `GET /donor_dashboard` - Donor dashboard
- `GET /ngo_dashboard` - NGO dashboard
- `GET /volunteer_dashboard` - Volunteer dashboard

### Operations
- `POST /submit_food_request` - Submit food donation
- `POST /accept_ngo` - Accept NGO request
- `POST /ngo_accept_donation` - NGO accepts donation
- `GET /progress` - View progress tracking
- `GET /live_tracking` - Live volunteer tracking

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Contact

For questions or support, please open an issue in the GitHub repository.
