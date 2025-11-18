#!/usr/bin/env python3
"""
Script to populate the FoodBridge database with sample data for testing.
"""

import sqlite3
import random

def populate_sample_data():
    """Populate database with sample NGOs, volunteers, and food requests"""

    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()

    # Sample NGOs data (Chennai locations)
    ngos_data = [
        {
            'firebase_uid': 'ngo1_uid',
            'name': 'Helping Hands Foundation',
            'email': 'contact@helpinghands.org',
            'registration_number': 'NGO001',
            'society_cert': 'cert1.pdf',
            'trust_deed': 'trust1.pdf',
            'section8_cert': 'section1.pdf',
            'verified': 1,
            'auto_verified': 1,
            'lat': 13.0827,
            'lon': 80.2707,
            'address': '456 NGO Street, Chennai'
        },
        {
            'firebase_uid': 'ngo2_uid',
            'name': 'Food for All',
            'email': 'info@foodforall.org',
            'registration_number': 'NGO002',
            'society_cert': 'cert2.pdf',
            'trust_deed': 'trust2.pdf',
            'section8_cert': 'section2.pdf',
            'verified': 1,
            'auto_verified': 1,
            'lat': 13.0927,
            'lon': 80.2807,
            'address': '789 Welfare Rd, Chennai'
        },
        {
            'firebase_uid': 'ngo3_uid',
            'name': 'City Harvest',
            'email': 'outreach@cityharvest.net',
            'registration_number': 'NGO003',
            'society_cert': 'cert3.pdf',
            'trust_deed': 'trust3.pdf',
            'section8_cert': 'section3.pdf',
            'verified': 1,
            'auto_verified': 1,
            'lat': 13.0727,
            'lon': 80.2607,
            'address': '321 Community Ave, Chennai'
        }
    ]

    # Insert NGOs
    for ngo in ngos_data:
        cursor.execute('''
            INSERT OR REPLACE INTO ngos
            (firebase_uid, name, email, registration_number, society_cert, trust_deed,
             section8_cert, verified, auto_verified, lat, lon, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ngo['firebase_uid'], ngo['name'], ngo['email'], ngo['registration_number'],
            ngo['society_cert'], ngo['trust_deed'], ngo['section8_cert'],
            ngo['verified'], ngo['auto_verified'], ngo['lat'], ngo['lon'], ngo['address']
        ))

    # Sample volunteers data
    volunteers_data = [
        {
            'firebase_uid': 'vol1_uid',
            'name': 'Raj Kumar',
            'email': 'raj.volunteer@gmail.com',
            'phone': '+91 98765 43210',
            'skills': 'Driving, Food handling',
            'availability': 'Weekdays 9AM-5PM',
            'verified': 1,
            'lat': 13.0850,
            'lon': 80.2750,
            'average_rating': 4.5,
            'total_ratings': 12
        },
        {
            'firebase_uid': 'vol2_uid',
            'name': 'Priya Sharma',
            'email': 'priya.volunteer@gmail.com',
            'phone': '+91 98765 43211',
            'skills': 'Logistics, Communication',
            'availability': 'Weekends 10AM-4PM',
            'verified': 1,
            'lat': 13.0900,
            'lon': 80.2850,
            'average_rating': 4.8,
            'total_ratings': 8
        },
        {
            'firebase_uid': 'vol3_uid',
            'name': 'Arun Patel',
            'email': 'arun.volunteer@gmail.com',
            'phone': '+91 98765 43212',
            'skills': 'Driving, Heavy lifting',
            'availability': 'Daily 8AM-6PM',
            'verified': 1,
            'lat': 13.0750,
            'lon': 80.2650,
            'average_rating': 4.2,
            'total_ratings': 15
        }
    ]

    # Insert volunteers
    for vol in volunteers_data:
        cursor.execute('''
            INSERT OR REPLACE INTO volunteers
            (firebase_uid, name, email, phone, skills, availability, verified,
             lat, lon, average_rating, total_ratings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vol['firebase_uid'], vol['name'], vol['email'], vol['phone'],
            vol['skills'], vol['availability'], vol['verified'],
            vol['lat'], vol['lon'], vol['average_rating'], vol['total_ratings']
        ))

    # Sample food requests data
    food_requests_data = [
        {
            'ngo_id': 1,  # Helping Hands Foundation
            'donor_name': 'John Restaurant',
            'food_type': 'Rice and Curry',
            'quantity': 50,
            'urgency': 'High',
            'location': 'T. Nagar, Chennai',
            'pickup_lat': 13.0850,
            'pickup_lon': 80.2750,
            'contact_person': 'John Doe',
            'contact_phone': '+91 98765 43213',
            'status': 'assigned',
            'assigned_volunteer_id': 1,  # Raj Kumar
        },
        {
            'ngo_id': 2,  # Food for All
            'donor_name': 'Green Hotel',
            'food_type': 'Bread and Vegetables',
            'quantity': 30,
            'urgency': 'Medium',
            'location': 'Adyar, Chennai',
            'pickup_lat': 13.0900,
            'pickup_lon': 80.2850,
            'contact_person': 'Jane Smith',
            'contact_phone': '+91 98765 43214',
            'status': 'in_transit',
            'assigned_volunteer_id': 2,  # Priya Sharma
        },
        {
            'ngo_id': 3,  # City Harvest
            'donor_name': 'Sunshine Bakery',
            'food_type': 'Cakes and Pastries',
            'quantity': 25,
            'urgency': 'Low',
            'location': 'Velachery, Chennai',
            'pickup_lat': 13.0750,
            'pickup_lon': 80.2650,
            'contact_person': 'Mike Johnson',
            'contact_phone': '+91 98765 43215',
            'status': 'collected',
            'assigned_volunteer_id': 3,  # Arun Patel
        }
    ]

    # Insert food requests
    for req in food_requests_data:
        cursor.execute('''
            INSERT OR REPLACE INTO food_requests
            (ngo_id, donor_name, food_type, quantity, urgency, location,
             pickup_lat, pickup_lon, contact_person, contact_phone, status, assigned_volunteer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            req['ngo_id'], req['donor_name'], req['food_type'], req['quantity'],
            req['urgency'], req['location'], req['pickup_lat'], req['pickup_lon'],
            req['contact_person'], req['contact_phone'], req['status'], req['assigned_volunteer_id']
        ))

    # Sample volunteer ratings
    ratings_data = [
        {'ngo_id': 1, 'volunteer_id': 1, 'rating': 5, 'review': 'Excellent service'},
        {'ngo_id': 1, 'volunteer_id': 1, 'rating': 4, 'review': 'Good communication'},
        {'ngo_id': 2, 'volunteer_id': 2, 'rating': 5, 'review': 'Very reliable'},
        {'ngo_id': 3, 'volunteer_id': 3, 'rating': 4, 'review': 'Timely delivery'},
    ]

    # Insert ratings
    for rating in ratings_data:
        cursor.execute('''
            INSERT INTO volunteer_ratings (ngo_id, volunteer_id, rating, review)
            VALUES (?, ?, ?, ?)
        ''', (rating['ngo_id'], rating['volunteer_id'], rating['rating'], rating['review']))

    conn.commit()
    conn.close()
    print("Sample data populated successfully!")

if __name__ == '__main__':
    populate_sample_data()
