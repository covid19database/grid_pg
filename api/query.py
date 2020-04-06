import requests

example = {
    "start_time": "2020-04-01T00:00:00",
    "end_time": "2020-04-04T00:00:00",
    "coordinates": [
        {
            "lat": 37.8123177,
            "lon": -122.2728663
        },
    ],
}

r = requests.post('http://localhost:8080/grid', json=example)
print(r.json())
