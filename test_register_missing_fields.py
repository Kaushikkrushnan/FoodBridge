import urllib.request
import json

# Test missing name
data = {
    'email': 'test@example.com',
    'registration_number': 'TEST123',
    'id_token': 'fake_token_for_testing'
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
