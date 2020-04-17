import time
import requests

example = {
    "timestamp": "2020-04-01T00:30:00",
    "location": "849V0000+"
}

t1 = time.time()
r = requests.post('http://localhost:5001/get', json=example)
if not r.ok:
    print(r.content)
else:
    print(r.json())
print(time.time() - t1)

example = {
    "timestamp": "2020-04-01T00:30:00",
    "location": "849VM5FP+"
}

t1 = time.time()
r = requests.post('http://localhost:5001/get', json=example)
if not r.ok:
    print(r.content)
else:
    print(r.json())
print(time.time() - t1)
