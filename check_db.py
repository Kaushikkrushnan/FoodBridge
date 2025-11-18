import sqlite3

conn = sqlite3.connect('database/app.db')
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

# Check ngos table schema
cursor.execute("PRAGMA table_info(ngos)")
ngos_schema = cursor.fetchall()
print('NGOs table schema:', ngos_schema)

# Check some data
cursor.execute("SELECT COUNT(*) FROM ngos")
count = cursor.fetchone()[0]
print('Total NGOs:', count)

if count > 0:
    cursor.execute("SELECT id, name, email, registration_number, verified, auto_verified FROM ngos LIMIT 5")
    rows = cursor.fetchall()
    print('Sample NGOs:', rows)

conn.close()
