import sqlite3
import os
from db import get_volunteer_db_connection
from math import radians, cos, sin, asin, sqrt

ASSIGNMENT_DB_PATH = os.path.join(os.path.dirname(__file__), 'assignment.db')

def haversine(lat1, lon1, lat2, lon2):
    # Calculate the great circle distance between two points on the earth (km)
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

def allocate_volunteer_to_request(request_id, pickup_lat, pickup_lon):
    # Find available volunteers closest to the pickup location
    vconn = get_volunteer_db_connection()
    vcursor = vconn.cursor()
    vcursor.execute("SELECT id, name, lat, lon, is_available FROM volunteers WHERE is_available = 1 AND lat IS NOT NULL AND lon IS NOT NULL")
    volunteers = vcursor.fetchall()
    vconn.close()
    best_vol = None
    min_dist = float('inf')
    for v in volunteers:
        dist = haversine(pickup_lat, pickup_lon, v['lat'], v['lon'])
        if dist < min_dist:
            min_dist = dist
            best_vol = v
    if best_vol:
        # Update assignment_db with volunteer info
        conn = sqlite3.connect(ASSIGNMENT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE food_donor_requests SET volunteer_id = ?, volunteer_name = ?, volunteer_allocated_time = CURRENT_TIMESTAMP WHERE id = ?
        """, (best_vol['id'], best_vol['name'], request_id))
        cursor.execute("""
            UPDATE ngo_assignments SET volunteer_id = ?, volunteer_name = ?, volunteer_allocated_time = CURRENT_TIMESTAMP WHERE id = (SELECT assignment_id FROM food_donor_requests WHERE id = ?)
        """, (best_vol['id'], best_vol['name'], request_id))
        conn.commit()
        conn.close()
        return best_vol['id'], best_vol['name']
    return None, None

if __name__ == "__main__":
    # Example usage: allocate_volunteer_to_request(request_id, pickup_lat, pickup_lon)
    pass
