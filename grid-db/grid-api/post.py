import requests
import hashlib
import os
import random
from calendar import monthrange
from datetime import datetime

random.seed(12345)

oakland_pluscodes = [
    '849VVP47+',
    '849VVP48+',
    '849VVP49+',
    '849VVP4C+',
    '849VVP4F+',
    '849VVP4G+',
    '849VVP4H+',
    '849VVP37+',
    '849VVP38+',
    '849VVP39+',
    '849VVP3C+',
    '849VVP3F+',
    '849VVP3G+',
    '849VVP3H+',
    '849VVP3J+',
    '849VVP28+',
    '849VVP29+',
    '849VVP2C+',
    '849VVP2G+',
    '849VVP2H+',
    '849VVP2J+'
]


def random_date(year, month_range):
    month = random.choice(month_range)
    day = random.randint(1, monthrange(year, month)[1])
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    ts = datetime(year, month, day, hour, minute)
    return ts.strftime('%Y-%m-%dT%H:%M:%S')


def nonce():
    h = hashlib.sha256()
    h.update(os.urandom(32))
    return h.hexdigest()


def generate_data(n):
    for i in range(n):
        if i % 100 == 0:
            print(f'Generated {i}')
        yield {
            "nonce": nonce(),
            "timestamp": random_date(2020, [4]),
            "location": random.choice(oakland_pluscodes),
            "attributes": {
                "symptom_coughing": random.random() < 0.2,
                "symptom_sore_throat": random.random() < 0.1,
                "infected_tested": random.random() < 0.05,
                "had_mask": random.random() < 0.50,
                "had_gloves": random.random() < 0.30
            }
        }


datas = [
    {
        "nonce": nonce(),
        "timestamp": "2020-04-04T12:17:00",
        "location": "849VRPCP+",
        "attributes": {
            "had_mask": True,
            "symptom_coughing": False
        },
    },
    {
        "nonce": nonce(),
        "timestamp": "2020-04-04T12:01:00",
        "location": "849VRPCP+",
        "attributes": {
            "had_mask": True,
            "symptom_coughing": True
        },
    },
    {
        "nonce": nonce(),
        "timestamp": "2020-04-04T13:42:00",
        "location": "849VRPCH+",
        "attributes": {
            "had_mask": False,
            "infected_tested": True
        },
    },
    {
        "nonce": nonce(),
        "timestamp": "2020-04-05T11:30:00",
        "location": "849VRPCH+",
        "attributes": {
            "had_mask": False,
            "had_gloves": True
        },
    }
]

for ex in datas:
    r = requests.post('http://localhost:5001/add', json=ex)
    if not r.ok:
        print(str(r.content))
for ex in generate_data(1000000):
    r = requests.post('http://localhost:5001/add', json=ex)
    if not r.ok:
        print(str(r.content))
