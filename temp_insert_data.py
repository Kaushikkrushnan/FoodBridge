import sqlite3

conn = sqlite3.connect('database/app.db')
cursor = conn.cursor()

# Insert data from food_requests into food_donors
cursor.execute('''
    INSERT INTO food_donors (organization_name, food_type, quantity, ready_for_pickup_time, pickup_location, category, cuisine_type, spice_level, pickup_lat, pickup_lon, status, assigned_volunteer_id, selected_ngo_id, created_at)
    VALUES
    ('John Doe', 'Pizza', '10 slices', '2024-01-20 18:00:00', 'Downtown', 'non-vegetarian', 'italian', 'mild', NULL, NULL, 'requested', NULL, NULL, '2024-01-20 17:00:00'),
    ('Jane Smith', 'Rice and Curry', '20 kg', '2024-01-21 12:00:00', 'Suburb', 'vegetarian', 'south_indian', 'medium', NULL, NULL, 'assigned', 1, NULL, '2024-01-21 11:00:00'),
    ('Bob Johnson', 'Bread', '50 loaves', '2024-01-22 09:00:00', 'City Center', 'vegetarian', 'western', 'mild', NULL, NULL, 'collected', 2, NULL, '2024-01-22 08:00:00'),
    ('Alice Brown', 'Noodles', '30 kg', '2024-01-23 14:00:00', 'Mall', 'vegetarian', 'chinese', 'medium', NULL, NULL, 'in_transit', 1, NULL, '2024-01-23 13:00:00'),
    ('Charlie Wilson', 'Chapati', '40 kg', '2024-01-24 16:00:00', 'Temple', 'vegetarian', 'north_indian', 'mild', NULL, NULL, 'delivered', 2, NULL, '2024-01-24 15:00:00')
''')

conn.commit()
conn.close()
print('Inserted food_requests data into food_donors.')
