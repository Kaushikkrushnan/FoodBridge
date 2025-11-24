import sqlite3
import csv
import os
import uuid

# Path to the CSV file
csv_file = 'Datasets/ngo_run_Home_May_2025.csv'

# Connect to auth.db
conn = sqlite3.connect('database/auth.db')
cursor = conn.cursor()

# Clear existing data if any
cursor.execute('DELETE FROM users')

# Read CSV and populate
with open(csv_file, 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        district = row['Districts'].strip().replace(' ', '_')
        num_institutions = int(row['No. of Instutition'])
        for i in range(1, num_institutions + 1):
            name = f"NGO {district} {i}"
            email = f"ngo{district.lower()}{i}@example.com"
            registration_number = f"REG{district.upper()}{i:03d}"
            firebase_uid = str(uuid.uuid4())  # Generate a fake UID
            verified = 1
            auto_verified = 0
            cursor.execute('''
                INSERT INTO users (firebase_uid, email, name, registration_number, verified, auto_verified)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (firebase_uid, email, name, registration_number, verified, auto_verified))

conn.commit()
conn.close()

