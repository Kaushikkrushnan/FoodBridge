import sqlite3
import csv
import os

VOLUNTEER_DB_PATH = os.path.join(os.path.dirname(__file__), 'volunteer.db')
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Datasets', 'volunteers_sample.csv')

def import_volunteers_from_csv():
    conn = sqlite3.connect(VOLUNTEER_DB_PATH)
    cursor = conn.cursor()
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute('''
                INSERT INTO volunteers (name, email, phone, availability, verified, created_at)
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ''', (
                row.get('name', 'Unknown'),
                row.get('email', ''),
                row.get('phone', ''),
                row.get('availability', ''),
            ))
    conn.commit()
    conn.close()
    print("Volunteer data imported from CSV.")

if __name__ == "__main__":
    import_volunteers_from_csv()
