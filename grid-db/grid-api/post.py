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


def random_pluscode():
    pfx = '849V'
    valid_chars = ['2', '3', '4', '5', '6', '7', '8', '9', 'C', 'F', 'G',
                   'H', 'J', 'M', 'P', 'Q', 'R', 'V', 'W', 'X']
    first_part = ''.join([random.choice(valid_chars) for i in range(4)])
    last_part = ''.join([random.choice(valid_chars) for i in range(2)])
    return f"{pfx}{first_part}+{last_part}"


def nonce():
    h = hashlib.sha256()
    h.update(os.urandom(32))
    return h.hexdigest()


def random_attribute():
    n = random.random()
    if n < 0.5:
        return {'symptomatic': random.randint(0, 10)}
    elif n < 0.8:
        return {'diagnosed': random.randint(0, 10)}
    else:
        return {'confirmed': random.randint(0, 10)}


def generate_data(n):
    for i in range(n):
        if i % 100 == 0:
            print(f'Generated {i}')
        yield {
            "nonce": nonce(),
            "timestamp": random_date(2020, [4]),
            "location": random_pluscode(),
            "attributes": random_attribute()
        }


for ex in generate_data(1000000):
    r = requests.post('http://localhost:5001/put-inc', json=ex)
    if not r.ok:
        print(str(r.content))
