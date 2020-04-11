import requests

example = {
    "timestamp": "2020-04-05T11:30:00",
    "location": "849V0000+"
}

r = requests.post('http://localhost:5001/query', json=example)
if not r.ok:
    print(r.content)
else:
    print(r.json())
