import sqlite3

conn = sqlite3.connect('database/app.db')
cursor = conn.cursor()

# Add missing columns to food_donors table
try:
    cursor.execute('ALTER TABLE food_donors ADD COLUMN pickup_lat REAL')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE food_donors ADD COLUMN pickup_lon REAL')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE food_donors ADD COLUMN status TEXT DEFAULT 'available'")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE food_donors ADD COLUMN assigned_volunteer_id INTEGER')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE food_donors ADD COLUMN selected_ngo_id INTEGER')
except sqlite3.OperationalError:
    pass

conn.commit()
conn.close()
print('Added missing columns to food_donors table.')
