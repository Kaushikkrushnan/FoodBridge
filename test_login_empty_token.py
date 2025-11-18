import urllib.request
import json

# Test empty token
data = {
    'id_token': 'invalid_token'
}

json_data = json.dumps(data).encode('utf-8')
req = urllib.request.Request('http://localhost:5001/login_ngo', data=json_data, headers={'Content-Type': 'application/json'})

try:
    response = urllib.request.urlopen(req)
    print('Status:', response.getcode())
    print('Response:', response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code)
    print('Response:', e.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)
