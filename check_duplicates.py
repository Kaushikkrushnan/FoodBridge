import sqlite3

conn = sqlite3.connect('database/app.db')
cursor = conn.cursor()

# Check for duplicates with the test name
cursor.execute('SELECT COUNT(*) FROM ngos WHERE name = ?', ('fhqadjlghaz',))
count = cursor.fetchone()[0]
print('Duplicate count for "fhqadjlghaz":', count)

cursor.execute('SELECT * FROM ngos WHERE name = ? LIMIT 3', ('fhqadjlghaz',))
rows = cursor.fetchall()
print('Sample duplicates:', rows)

# Check total NGOs
cursor.execute('SELECT COUNT(*) FROM ngos')
total = cursor.fetchone()[0]
print('Total NGOs:', total)

conn.close()
