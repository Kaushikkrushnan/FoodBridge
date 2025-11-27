"""
Utility module for distance calculation and ETA computation.
Uses Haversine formula for accurate distance calculation between coordinates.
"""
import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth using the Haversine formula.
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
    
    Returns:
        Distance in kilometers (float)
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance_km = R * c
    return round(distance_km, 2)


def calculate_eta_minutes(distance_km, speed_kmh=30):
    """
    Calculate estimated time of arrival based on distance and average speed.
    
    Args:
        distance_km: Distance in kilometers
        speed_kmh: Average speed in km/h (default: 30 km/h for city driving)
    
    Returns:
        ETA in minutes (integer)
    """
    if distance_km is None:
        return None
    
    if distance_km <= 0:
        return 0
    
    # Calculate time in hours, then convert to minutes
    time_hours = distance_km / speed_kmh
    eta_minutes = int(round(time_hours * 60))
    
    return eta_minutes


def add_distance_and_eta(items, user_lat, user_lon, lat_field='lat', lon_field='lon'):
    """
    Add distance_km and eta_minutes to a list of items based on user's location.
    
    Args:
        items: List of dictionaries containing lat/lon fields
        user_lat: User's latitude
        user_lon: User's longitude
        lat_field: Name of latitude field in items (default: 'lat')
        lon_field: Name of longitude field in items (default: 'lon')
    
    Returns:
        List of items with distance_km and eta_minutes added, sorted by distance (nearest first)
    """
    if user_lat is None or user_lon is None:
        # If user location is not set, return items with None distance/ETA
        for item in items:
            item['distance_km'] = None
            item['eta_minutes'] = None
        return items
    
    for item in items:
        item_lat = item.get(lat_field)
        item_lon = item.get(lon_field)
        
        distance = haversine_distance(user_lat, user_lon, item_lat, item_lon)
        item['distance_km'] = distance
        item['eta_minutes'] = calculate_eta_minutes(distance)
    
    # Sort by distance (items with None distance go to the end)
    items.sort(key=lambda x: (x['distance_km'] is None, x['distance_km'] if x['distance_km'] is not None else float('inf')))
    
    return items


def format_distance(distance_km):
    """
    Format distance for display.
    
    Args:
        distance_km: Distance in kilometers
    
    Returns:
        Formatted string (e.g., "2.8 km" or "Location not set")
    """
    if distance_km is None:
        return "Location not set"
    return f"{distance_km} km"


def format_eta(eta_minutes):
    """
    Format ETA for display.
    
    Args:
        eta_minutes: ETA in minutes
    
    Returns:
        Formatted string (e.g., "6 minutes" or "N/A")
    """
    if eta_minutes is None:
        return "N/A"
    if eta_minutes == 0:
        return "< 1 minute"
    if eta_minutes == 1:
        return "1 minute"
    return f"{eta_minutes} minutes"
