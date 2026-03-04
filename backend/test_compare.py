import requests, json

print('Starting comparison engine test...')
r = requests.post('http://localhost:8000/api/v1/auth/login', json={'unique_user_id':'rahul_f1','date_of_birth':'1995-10-21'})
token = r.json().get('access_token')

if not token:
    print('Failed to login.')
    exit(1)

headers = {'Authorization': f'Bearer {token}'}

print('\n=== Fetching /compare/AAPL ===')
print('This will take ~10 seconds as it fetches fundamentals and risk for AAPL + 3 peers...')
res = requests.get('http://localhost:8000/api/v1/compare/AAPL', headers=headers)

if res.status_code == 200:
    print(json.dumps(res.json(), indent=2))
else:
    print(res.status_code, res.text)
