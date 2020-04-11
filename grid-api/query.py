import requests

example = {
    "timestamp": "2020-04-05T11:30:00",
    "location": "849VRPCH"
}

r = requests.post('http://localhost:5000/query', json=example)
if not r.ok:
    print(r.content)
else:
    print(r.json())
