import requests

example = {
    "timestamp": "2020-04-01T00:30:00",
    "location": "849V0000+"
}

r = requests.post('http://localhost:5001/get', json=example)
if not r.ok:
    print(r.content)
else:
    print(r.json())

example = {
    "timestamp": "2020-04-01T00:30:00",
    "location": "849VM5FP+"
}

r = requests.post('http://localhost:5001/get', json=example)
if not r.ok:
    print(r.content)
else:
    print(r.json())
