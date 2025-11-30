"""
Add Chennai-based mock data for testing FoodBridge.
This script adds:
- Chennai coordinates to existing NGOs
- Test food donors with Chennai locations
- Sample food donation requests
"""
import sqlite3
import os

# Chennai area locations for NGOs
CHENNAI_NGO_LOCATIONS = [
    # (id, lat, lon, address)
    (1, 13.0827, 80.2707, "T. Nagar, Chennai, Tamil Nadu"),      # Anna Daanam Trust - T.Nagar
    (2, 13.0339, 80.2699, "Mylapore, Chennai, Tamil Nadu"),       # Care & Share Foundation - Mylapore
    (4, 13.0012, 80.2565, "Adyar, Chennai, Tamil Nadu"),          # Helping Hands Society - Adyar
    (5, 13.0850, 80.2101, "Anna Nagar, Chennai, Tamil Nadu"),     # Community Kitchen Trust - Anna Nagar
    (39, 13.0418, 80.2341, "Nungambakkam, Chennai, Tamil Nadu"),  # Test NGO - Nungambakkam
    (40, 13.1067, 80.2842, "Perambur, Chennai, Tamil Nadu"),      # New Test NGO - Perambur
    (41, 13.0674, 80.2376, "Kodambakkam, Chennai, Tamil Nadu"),   # Unique Test NGO - Kodambakkam
    (42, 12.9908, 80.2158, "Guindy, Chennai, Tamil Nadu"),        # Another Unique Test NGO - Guindy
]

# Chennai area food donors for testing
CHENNAI_FOOD_DONORS = [
    # (organization_name, email, phone, food_type, quantity, pickup_location, lat, lon, category)
    ("Chennai Grand Hotel", "grandhotel@example.com", "9876543210", "Biryani & Rice", "50 servings", "Egmore, Chennai", 13.0792, 80.2615, "non_vegetarian"),
    ("South Indian Delights", "sidel@example.com", "9876543211", "Idli & Dosa", "100 servings", "Besant Nagar, Chennai", 13.0002, 80.2668, "vegetarian"),
    ("City Bakery", "citybakery@example.com", "9876543212", "Bread & Pastries", "30 loaves", "Velachery, Chennai", 12.9815, 80.2180, "vegetarian"),
    ("Marina Restaurant", "marina@example.com", "9876543213", "Fish Curry & Rice", "40 servings", "Marina Beach, Chennai", 13.0543, 80.2822, "non_vegetarian"),
    ("Vegetarian Paradise", "vegparadise@example.com", "9876543214", "Sambar Rice & Curd Rice", "60 servings", "Vadapalani, Chennai", 13.0519, 80.2121, "vegetarian"),
]

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
    print(f"Adding Chennai mock data to: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Update NGO locations with Chennai coordinates
    print("\n📍 Updating NGO locations with Chennai coordinates...")
    for ngo_id, lat, lon, address in CHENNAI_NGO_LOCATIONS:
        cursor.execute('''
            UPDATE ngos SET lat = ?, lon = ?, address = ? WHERE id = ?
        ''', (lat, lon, address, ngo_id))
        if cursor.rowcount > 0:
            print(f"  ✓ Updated NGO {ngo_id}: {address}")
    
    # Add test food donors
    print("\n🍽️ Adding Chennai food donors...")
    for donor in CHENNAI_FOOD_DONORS:
        # Check if already exists
        cursor.execute('SELECT id FROM food_donors WHERE email = ?', (donor[1],))
        if cursor.fetchone():
            print(f"  - Skipping {donor[0]} (already exists)")
            continue
        
        cursor.execute('''
            INSERT INTO food_donors (
                organization_name, email, phone, food_type, quantity, 
                pickup_location, pickup_lat, pickup_lon, category, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'available')
        ''', donor)
        print(f"  ✓ Added {donor[0]} at {donor[5]}")
    
    conn.commit()
    conn.close()
    print("\n✅ Chennai mock data added successfully!")
    
    # Print test credentials
    print("\n" + "="*60)
    print("📋 TEST CREDENTIALS")
    print("="*60)
    print("""
🔵 NGO Login (Use Firebase test token):
   Token: fake_token_for_testing
   This will log you in as "Test NGO" (id=1)
   
   OR use existing verified NGOs by email:
   - anna@example.com (Anna Daanam Trust, T.Nagar)
   - care@example.com (Care & Share Foundation, Mylapore)
   - helping@example.com (Helping Hands Society, Adyar)
   - community@example.com (Community Kitchen Trust, Anna Nagar)

🟢 Food Donor Login (Name + Phone):
   - Chennai Grand Hotel / 9876543210 (Egmore)
   - South Indian Delights / 9876543211 (Besant Nagar)
   - City Bakery / 9876543212 (Velachery)
   - Marina Restaurant / 9876543213 (Marina Beach)
   - Vegetarian Paradise / 9876543214 (Vadapalani)

🟡 Volunteer Login:
   - Currently using test mode (auto-simulated)

📍 Chennai Locations Used:
   - T.Nagar (13.0827, 80.2707)
   - Mylapore (13.0339, 80.2699)
   - Adyar (13.0012, 80.2565)
   - Anna Nagar (13.0850, 80.2101)
   - Nungambakkam (13.0418, 80.2341)
   - Egmore (13.0792, 80.2615)
   - Besant Nagar (13.0002, 80.2668)
   - Velachery (12.9815, 80.2180)
   - Marina Beach (13.0543, 80.2822)
   - Vadapalani (13.0519, 80.2121)
""")
    print("="*60)

if __name__ == '__main__':
    migrate()
