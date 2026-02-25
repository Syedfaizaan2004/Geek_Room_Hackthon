import urllib.request, json
req = urllib.request.Request(
    'http://127.0.0.1:8000/agent',
    data=b'{"query":"Deep research on TCS.NS", "mode":"deep"}',
    headers={'Content-Type': 'application/json'}
)
try:
    response = urllib.request.urlopen(req)
    print("STATUS:", response.status)
    print(response.read().decode())
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'read'):
        print(e.read().decode())
