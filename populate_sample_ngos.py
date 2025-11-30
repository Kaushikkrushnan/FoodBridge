"""
Populate sample data for testing the FoodBridge application.
Adds sample NGOs and food donors with location data.
"""
import sqlite3
import os

# Database paths
DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
AUTH_DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'auth.db')


def populate_sample_ngos():
    """Add sample NGOs to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if NGOs already exist
    existing = cursor.execute('SELECT COUNT(*) as count FROM ngos').fetchone()
    if existing['count'] > 0:
        print(f"NGOs table already has {existing['count']} records. Skipping...")
        conn.close()
        return
    
    # Sample NGOs in Chennai with lat/lon
    sample_ngos = [
        ('Helping Hands Foundation', 'helping.hands@example.com', 'REG001', None, None, None, 1, 1, 'No. 45, Anna Salai, Chennai', 13.0827, 80.2707),
        ('Food For All Trust', 'foodforall@example.com', 'REG002', None, None, None, 1, 1, 'No. 78, Mount Road, Chennai', 13.0612, 80.2612),
        ('Care & Share NGO', 'careshare@example.com', 'REG003', None, None, None, 1, 1, 'No. 23, T Nagar, Chennai', 13.0418, 80.2341),
        ('Chennai Food Bank', 'chennai.foodbank@example.com', 'REG004', None, None, None, 1, 1, 'No. 56, Velachery, Chennai', 12.9815, 80.2180),
        ('Hope Foundation', 'hope.foundation@example.com', 'REG005', None, None, None, 1, 1, 'No. 12, Adyar, Chennai', 13.0067, 80.2565),
        ('Akshaya Patra Chennai', 'akshayapatra@example.com', 'REG006', None, None, None, 1, 1, 'No. 89, Guindy, Chennai', 13.0108, 80.2212),
        ('Feed The Need', 'feedtheneed@example.com', 'REG007', None, None, None, 1, 1, 'No. 34, Mylapore, Chennai', 13.0339, 80.2676),
        ('Community Kitchen', 'community.kitchen@example.com', 'REG008', None, None, None, 1, 1, 'No. 67, Perambur, Chennai', 13.1170, 80.2420),
    ]
    
    for ngo in sample_ngos:
        cursor.execute('''
            INSERT INTO ngos (name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified, address, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ngo)
    
    conn.commit()
    print(f"Added {len(sample_ngos)} sample NGOs to the database.")
    conn.close()


def populate_auth_ngos():
    """Add sample NGOs to the auth database for login."""
    conn = sqlite3.connect(AUTH_DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if users already exist
    existing = cursor.execute('SELECT COUNT(*) as count FROM users').fetchone()
    if existing['count'] > 0:
        print(f"Auth users table already has {existing['count']} records. Skipping...")
        conn.close()
        return
    
    # Sample NGOs for auth
    sample_users = [
        ('firebase_uid_1', 'Helping Hands Foundation', 'helping.hands@example.com', 'REG001', '', '', '', 1, 1),
        ('firebase_uid_2', 'Food For All Trust', 'foodforall@example.com', 'REG002', '', '', '', 1, 1),
        ('firebase_uid_3', 'Care & Share NGO', 'careshare@example.com', 'REG003', '', '', '', 1, 1),
    ]
    
    for user in sample_users:
        cursor.execute('''
            INSERT INTO users (firebase_uid, name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', user)
    
    conn.commit()
    print(f"Added {len(sample_users)} sample users to auth database.")
    conn.close()


def populate_sample_donors():
    """Add sample food donors to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if donors already exist
    existing = cursor.execute('SELECT COUNT(*) as count FROM food_donors').fetchone()
    if existing['count'] > 0:
        print(f"Food donors table already has {existing['count']} records. Skipping...")
        conn.close()
        return
    
    # Sample food donors with location
    sample_donors = [
        ('Chennai Bakery', None, '9876543210', '9876543210', 'Bike', 'No. 10, Egmore, Chennai', 13.0789, 80.2606),
        ('Hotel Saravana', None, '9876543211', '9876543211', 'Van', 'No. 25, Nungambakkam, Chennai', 13.0604, 80.2389),
        ('Restaurant Paradise', None, '9876543212', '9876543212', 'Car', 'No. 50, Alwarpet, Chennai', 13.0325, 80.2452),
        ('South Indian Cafe', None, '9876543213', '9876543213', 'Bike', 'No. 15, Kodambakkam, Chennai', 13.0510, 80.2248),
        ('The Kitchen Hub', None, '9876543214', '9876543214', 'Van', 'No. 80, Chetpet, Chennai', 13.0720, 80.2435),
    ]
    
    for donor in sample_donors:
        cursor.execute('''
            INSERT INTO food_donors (organization_name, email, phone, whatsapp_phone, vehicle_type, address, lat, lon, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', donor)
    
    conn.commit()
    print(f"Added {len(sample_donors)} sample food donors to the database.")
    conn.close()


if __name__ == "__main__":
    print("Populating sample data...")
    populate_sample_ngos()
    populate_auth_ngos()
    populate_sample_donors()
    print("Done!")
