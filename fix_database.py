"""
Fix database schema and populate sample data
"""
from db import get_db_connection
import sqlite3

def fix_database():
    """Drop and recreate tables with correct schema"""
    conn = get_db_connection()
    
    # Drop existing tables
    conn.execute('DROP TABLE IF EXISTS food_requests')
    conn.execute('DROP TABLE IF EXISTS volunteers')
    conn.execute('DROP TABLE IF EXISTS ngos')
    
    # Recreate NGOs table with correct schema
    conn.execute('''
        CREATE TABLE ngos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            registration_number TEXT,
            society_cert TEXT,
            trust_deed TEXT,
            section8_cert TEXT,
            verified INTEGER DEFAULT 0,
            auto_verified INTEGER DEFAULT 0
        )
    ''')
    
    # Recreate Volunteers table
    conn.execute('''
        CREATE TABLE volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            lat REAL,
            lon REAL,
            available_from TEXT,
            available_to TEXT,
            is_available INTEGER DEFAULT 1,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Recreate Food requests table
    conn.execute('''
        CREATE TABLE food_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT,
            food_type TEXT,
            quantity TEXT,
            pickup_location TEXT,
            pickup_lat REAL,
            pickup_lon REAL,
            pickup_time TEXT,
            status TEXT DEFAULT 'active',
            assigned_volunteer_id INTEGER,
            food_category TEXT,
            cuisine_type TEXT,
            spice_level TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database schema fixed!")


def populate_sample_data():
    """Insert sample data into all tables"""
    conn = get_db_connection()
    
    # Sample NGOs
    ngos_data = [
        ('Anna Daanam Trust', 'anna@example.com', 'TN/12345/2020', 'static/uploads/society_cert_1.pdf', 'static/uploads/trust_deed_1.pdf', 'static/uploads/section8_cert_1.pdf', 1, 0),
        ('Care & Share Foundation', 'care@example.com', 'TN/67890/2019', 'static/uploads/society_cert_2.pdf', 'static/uploads/trust_deed_2.pdf', 'static/uploads/section8_cert_2.pdf', 1, 0),
        ('Food for All NGO', 'foodforall@example.com', 'TN/11111/2021', 'static/uploads/society_cert_3.pdf', 'static/uploads/trust_deed_3.pdf', 'static/uploads/section8_cert_3.pdf', 0, 0),
        ('Helping Hands Society', 'helping@example.com', 'TN/22222/2018', 'static/uploads/society_cert_4.pdf', 'static/uploads/trust_deed_4.pdf', 'static/uploads/section8_cert_4.pdf', 1, 0),
        ('Community Kitchen Trust', 'community@example.com', 'TN/33333/2022', 'static/uploads/society_cert_5.pdf', 'static/uploads/trust_deed_5.pdf', 'static/uploads/section8_cert_5.pdf', 0, 0),
    ]
    
    for ngo in ngos_data:
        conn.execute('''
            INSERT INTO ngos (name, email, registration_number, society_cert, trust_deed, section8_cert, verified, auto_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ngo)
    
    # Sample Volunteers
    volunteers_data = [
        ('Priya Sharma', '+91 98765 43210', 13.0827, 80.2707, '09:00', '18:00', 1),
        ('Rahul Menon', '+91 90000 12345', 12.9716, 77.5946, '10:00', '20:00', 1),
        ('Anita Reddy', '+91 88888 99999', 13.0358, 80.2622, '08:00', '17:00', 1),
        ('Karthik Iyer', '+91 77777 88888', 12.9352, 77.6245, '14:00', '22:00', 1),
        ('Meera Patel', '+91 66666 77777', 13.0067, 80.2206, '07:00', '16:00', 0),
        ('Vikram Singh', '+91 55555 66666', 12.9141, 77.6412, '11:00', '21:00', 1),
    ]
    
    for vol in volunteers_data:
        conn.execute('''
            INSERT INTO volunteers (name, contact, lat, lon, available_from, available_to, is_available)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', vol)
    
    # Sample Food Requests
    food_requests_data = [
        ('FreshBites Bakery', 'Bread loaves', '50 loaves', 'T. Nagar, Chennai', 13.0358, 80.2622, '2024-01-15 18:00', 'active', None, 'vegetarian', 'western', 'mild'),
        ('Hotel GreenLeaf', 'Veg meal boxes', '30 boxes', 'Adyar, Chennai', 13.0067, 80.2206, '2024-01-15 19:30', 'active', None, 'vegetarian', 'indian', 'medium'),
        ('Sweet Delights', 'Cakes and pastries', '20 pieces', 'Velachery, Chennai', 12.9698, 80.2209, '2024-01-15 20:00', 'active', None, 'low_sugar', 'western', 'mild'),
        ('Spice Garden Restaurant', 'Biryani packets', '40 packets', 'Anna Nagar, Chennai', 13.0850, 80.2101, '2024-01-15 21:00', 'active', None, 'vegetarian', 'indian', 'spicy'),
        ('Cafe Mocha', 'Sandwiches', '25 sandwiches', 'Nungambakkam, Chennai', 13.0604, 80.2496, '2024-01-16 12:00', 'active', None, 'vegetarian', 'western', 'mild'),
        ('Dosa Corner', 'Dosa and idli', '60 pieces', 'Mylapore, Chennai', 13.0330, 80.2698, '2024-01-16 13:00', 'active', None, 'vegetarian', 'indian', 'mild'),
        ('Pizza Express', 'Pizza slices', '35 slices', 'OMR, Chennai', 12.9042, 80.2269, '2024-01-16 14:00', 'active', None, 'vegetarian', 'western', 'mild'),
        ('Curry House', 'Curry and rice', '45 plates', 'Tambaram, Chennai', 12.9249, 80.1000, '2024-01-16 15:00', 'active', None, 'vegetarian', 'indian', 'medium'),
    ]
    
    for req in food_requests_data:
        conn.execute('''
            INSERT INTO food_requests (donor_name, food_type, quantity, pickup_location, pickup_lat, pickup_lon, pickup_time, status, assigned_volunteer_id, food_category, cuisine_type, spice_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', req)
    
    conn.commit()
    conn.close()
    print("✅ Sample data populated successfully!")
    print("\n📊 Summary:")
    print("   - 5 NGOs (3 verified, 2 pending)")
    print("   - 6 Volunteers (5 available, 1 unavailable)")
    print("   - 8 Food Requests (all active)")


if __name__ == '__main__':
    fix_database()
    populate_sample_data()

