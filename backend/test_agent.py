import requests, json

print('Starting LangGraph Orchestration tests...')
r = requests.post('http://localhost:8000/api/v1/auth/login', json={'unique_user_id':'rahul_f1','date_of_birth':'1995-10-21'})
token = r.json().get('access_token')

if not token:
    print('Failed to login.')
    exit(1)

headers = {'Authorization': f'Bearer {token}'}

modes = ['quick', 'next_analysis', 'hidden_risk', 'compare', 'deep']

for mode in modes:
    print(f'\n=========================================')
    print(f'=== Executing Workflow: {mode.upper()} ===')
    print(f'=========================================')
    
    payload = {"ticker": "AAPL", "mode": mode}
    res = requests.post('http://localhost:8000/api/v1/analyze', headers=headers, json=payload)
    
    if res.status_code == 200:
        data = res.json()
        print(f"Execution Time: {data['execution_time_ms']}ms")
        
        # Print high-level keys returned in data
        keys = list(data['data'].keys())
        populated_keys = [k for k in keys if data['data'][k] is not None]
        print(f"Populated State Blocks: {populated_keys}")
        
        if mode == 'next_analysis':
            print(f"Recommendation: {data['data'].get('next_step_recommendation')}")
        elif mode == 'hidden_risk':
            risks = data['data'].get('risk', {}).get('hidden_risks', [])
            print(f"Hidden Risks Found: {len(risks)}")
    else:
        print(res.status_code, res.text)
