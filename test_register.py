import urllib.request
import json

data = {
    'name': 'Another Unique Test NGO',
    'email': 'anotheruniquetest@example.com',
    'registration_number': 'TN/99999/2023',
    'society_cert': 'static/uploads/society_1763348283_Screenshot_2025-09-16_174804.png',
    'trust_deed': 'static/uploads/trust_1763348288_Screenshot_2025-09-16_174828.png',
    'section8_cert': 'static/uploads/section8_1763348293_Screenshot_2025-09-16_174913.png',
    'id_token': 'fake_token_for_testing'  # Note: This is a fake token; in real scenario, use actual Firebase ID token
}

json_data = json.dumps(data).encode('utf-8')
req = urllib.request.Request('http://localhost:5001/register_ngo', data=json_data, headers={'Content-Type': 'application/json'})

try:
    response = urllib.request.urlopen(req)
    print('Status:', response.getcode())
    print('Response:', response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code)
    print('Response:', e.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)
