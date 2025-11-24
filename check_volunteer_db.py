from db import get_volunteer_db_connection

conn = get_volunteer_db_connection()
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="volunteers"')
result = cursor.fetchone()
conn.close()
print('volunteers table exists:', result is not None)
