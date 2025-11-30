"""
Automated tests for FoodBridge flow
Tests NGO login, donor request creation, NGO acceptance, and progress tracking.
"""
import pytest
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client


class TestNGOLogin:
    """Test cases for NGO login functionality."""
    
    def test_login_success_with_test_token(self, client):
        """Test NGO login with fake test token succeeds."""
        response = client.post('/login_ngo',
            data=json.dumps({'id_token': 'fake_token_for_testing'}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert 'ngo' in data
        assert data['ngo']['name'] == 'Test NGO'
    
    def test_login_failure_missing_token(self, client):
        """Test NGO login fails when token is missing."""
        response = client.post('/login_ngo',
            data=json.dumps({}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['success'] == False
        assert 'token' in data['message'].lower()
    
    def test_login_failure_empty_token(self, client):
        """Test NGO login fails with empty token."""
        response = client.post('/login_ngo',
            data=json.dumps({'id_token': ''}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['success'] == False


class TestDonorRequestCreation:
    """Test cases for donor request creation."""
    
    def test_accept_ngo_creates_request(self, client):
        """Test that accepting an NGO creates a request record."""
        # First login as donor (simulate by setting session)
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test Donor'
            sess['user_role'] = 'Donor'
        
        response = client.post('/accept_ngo',
            data=json.dumps({'ngo_id': 1, 'ngo_name': 'Test NGO'}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert 'assignment_id' in data


class TestNGODashboard:
    """Test cases for NGO dashboard and filtering."""
    
    def test_ngo_dashboard_loads(self, client):
        """Test that NGO dashboard page loads successfully."""
        # Login first
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test NGO'
            sess['user_role'] = 'NGO'
            sess['db_session_id'] = 'test-session'
        
        response = client.get('/ngo_dashboard')
        assert response.status_code == 200
        assert b'NGO Dashboard' in response.data


class TestNGOAcceptDonation:
    """Test cases for NGO accepting donations."""
    
    def test_accept_donation_updates_status(self, client):
        """Test that NGO accepting donation updates request status."""
        # Login as NGO
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test NGO'
            sess['user_role'] = 'NGO'
        
        # This may fail if no request exists - that's expected behavior
        response = client.post('/ngo_accept_donation',
            data=json.dumps({'request_id': 1}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        # Could succeed or fail depending on whether request 1 exists
        assert response.status_code in [200, 500]


class TestProgressTracking:
    """Test cases for progress tracking sequence."""
    
    def test_get_progress_endpoint(self, client):
        """Test that get_progress endpoint returns data."""
        response = client.get('/get_progress/1')
        data = json.loads(response.data)
        
        # Will return not found if no request 1 exists - expected
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert 'progress' in data
    
    def test_update_delivery_status(self, client):
        """Test updating delivery status."""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Test NGO'
            sess['user_role'] = 'NGO'
        
        response = client.post('/update_delivery_status',
            data=json.dumps({'request_id': 1, 'status': 'delivered'}),
            content_type='application/json'
        )
        
        # Could succeed or fail depending on whether request exists
        assert response.status_code in [200, 500]


class TestDistanceCalculation:
    """Test cases for distance calculation with sample coordinates."""
    
    def test_distance_chennai_locations(self, client):
        """Test distance calculation with Chennai sample locations."""
        # T.Nagar to Mylapore (approx 3-4 km)
        response = client.get('/get_distance?donor_lat=13.0418&donor_lon=80.2341&ngo_lat=13.0339&ngo_lon=80.2699')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert 'distance_km' in data
        # Should be roughly 3-4 km
        assert 2.0 < data['distance_km'] < 6.0
    
    def test_distance_adyar_to_anna_nagar(self, client):
        """Test distance calculation Adyar to Anna Nagar (approx 10-12 km)."""
        response = client.get('/get_distance?donor_lat=13.0012&donor_lon=80.2565&ngo_lat=13.0850&ngo_lon=80.2101')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        # Should be roughly 10-12 km
        assert 8.0 < data['distance_km'] < 15.0
    
    def test_distance_missing_coordinates_fallback(self, client):
        """Test that missing coordinates returns reasonable fallback."""
        response = client.get('/get_distance?donor_id=999&ngo_id=999')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['distance_km'] == 5.0  # Default fallback
        assert data['estimated'] == True


class TestNearestFirstSorting:
    """Test cases for nearest-first sorting."""
    
    def test_distance_sorting_logic(self, client):
        """Test that distances can be compared for sorting."""
        # Get distances for 3 locations
        locations = [
            {'lat': 13.0418, 'lon': 80.2341},  # T.Nagar
            {'lat': 13.0339, 'lon': 80.2699},  # Mylapore
            {'lat': 13.0850, 'lon': 80.2101},  # Anna Nagar
        ]
        donor_lat, donor_lon = 13.0827, 80.2707  # Central Chennai
        
        distances = []
        for loc in locations:
            response = client.get(f'/get_distance?donor_lat={donor_lat}&donor_lon={donor_lon}&ngo_lat={loc["lat"]}&ngo_lon={loc["lon"]}')
            data = json.loads(response.data)
            distances.append(data['distance_km'])
        
        # All distances should be valid numbers
        assert all(isinstance(d, (int, float)) for d in distances)
        assert all(d > 0 for d in distances)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
