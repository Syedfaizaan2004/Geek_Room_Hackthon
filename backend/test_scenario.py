import requests, json

print('Starting scenario engine test...')
r = requests.post('http://localhost:8000/api/v1/auth/login', json={'unique_user_id':'rahul_f1','date_of_birth':'1995-10-21'})
token = r.json().get('access_token')

if not token:
    print('Failed to login.')
    exit(1)

headers = {'Authorization': f'Bearer {token}'}

scenarios = ['recession', 'inflation', 'rate_hike', 'growth_slowdown']
for s in scenarios:
    print(f'\n=== Fetching /scenario/MSFT?type={s} ===')
    res = requests.get(f'http://localhost:8000/api/v1/scenario/MSFT?type={s}', headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f"Baseline Proj: {data['baseline_projection']} -> Adjusted Proj: {data['adjusted_projection']}")
        print(f"Baseline Risk: {data['baseline_risk_score']} -> Adjusted Risk: {data['adjusted_risk_score']}")
        print(f"Baseline Uncert: {data['baseline_uncertainty_percent']} -> Adjusted: {data['adjusted_uncertainty_percent']}")
        print(f"Reasoning: {data['impact_analysis']}")
    else:
        print(res.status_code, res.text)
