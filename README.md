# FoodBridge

Building a digital platform to connect surplus food sources with NGOs for real-time redistribution and waste reduction.

## 🚀 Features

### User Types
- **Food Donors**: Restaurants, bakeries, or individuals with surplus food
- **NGOs**: Organizations that collect and distribute food to those in need
- **Volunteers**: Transport volunteers who pick up and deliver food donations

### Key Functionality
- **Authentication System**: Separate login/registration for Food Donors, NGOs, and Volunteers
- **Food Donor Dashboard**: View available NGOs, request donations, track accepted requests
- **NGO Dashboard**: View pending food donation requests, accept donations, auto-assign volunteers
- **Volunteer Assignment**: Automatic assignment using Haversine formula for distance calculation
- **Live Progress Tracking**: Real-time tracking of donation status from pickup to delivery

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- SQLite (included with Python)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kaushikkrushnan/FoodBridge.git
   cd FoodBridge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   Open your browser and go to: `http://localhost:5001`

## 📁 Project Structure

```
FoodBridge/
├── app.py                 # Main Flask application
├── Templates/             # HTML templates
│   ├── index.html         # Homepage
│   ├── food_donor_registration.html
│   ├── food_donor_login.html
│   ├── Donor_dashboard.html
│   ├── NGO_login.html
│   ├── NGO_dashboard.html
│   └── ...
├── routes/                # Flask route blueprints
│   ├── auth_routes.py     # Authentication routes
│   ├── dashboard_routes.py
│   ├── donor_routes.py
│   └── ...
├── database/              # SQLite databases
│   ├── app.db             # Main database (food_donors, ngos tables)
│   └── assignment.db      # Volunteer assignments
├── static/                # Static files (CSS, JS, images)
└── requirements.txt       # Python dependencies
```

## 🔑 User Flows

### Food Donor Flow
1. Register at `/food_donor_register`
2. Login at `/food_donor_login`
3. View available NGOs on dashboard
4. Click "Review & Accept" to request an NGO
5. Track donation progress via "Live Progress Tracking"

### NGO Flow
1. Register at `/ngo_register`
2. Login at `/ngo_login` (with Firebase authentication)
3. View pending food donor requests
4. Click "Accept & Assign Volunteer" to accept donation
5. A volunteer is automatically assigned based on proximity
6. Track donation progress via "Live Progress Tracking"

### Volunteer Flow
1. Register at `/volunteer_register`
2. Login at `/volunteer_login`
3. View assigned pickup tasks on dashboard
4. Update task status as pickup progresses

## 🗄️ Database Schema

### food_donors table (app.db)
- id, name, phone, email, whatsapp_phone, vehicle_type, address

### ngos table (app.db)
- id, name, email, registration_number, password, primary_contact

### volunteers table (app.db)
- id, name, phone, email, latitude, longitude, is_available

## 🔧 Configuration

The application runs on port 5001 by default. To change this, modify `app.py`:
```python
app.run(debug=True, port=5001)
```

## 📸 Screenshots

### Food Donor Registration
![Food Donor Registration](https://github.com/user-attachments/assets/bdd8bcbe-2777-4753-9476-623361129a8d)

### Food Donor Login
![Food Donor Login](https://github.com/user-attachments/assets/b2224862-cf73-44bd-8a47-ec8be8bd2886)

### Donor Dashboard
![Donor Dashboard](https://github.com/user-attachments/assets/b14d3ca3-2dde-4f8f-9f72-c72ed32ff6dd)

### NGO Registration
![NGO Registration](https://github.com/user-attachments/assets/36fba620-a5bb-4016-ab61-9169d7874ad5)

### NGO Login
![NGO Login](https://github.com/user-attachments/assets/d2e34fa9-dc4a-4f7d-a2de-133f43497fd7)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.
