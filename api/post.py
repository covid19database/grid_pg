import requests

example = {
    "userid": 1,
    "timestamp": "2020-04-04T12:17:00",
    "feels_sick": False,
    "location_trace": [
        {
            "start_time": "2020-04-03T00:00:00",
            "end_time": "2020-04-03T04:00:00",
            "geographic_location": {
                "lat": 37.8123177,
                "lon": -122.2728663
            }
        },
        {
            "start_time": "2020-04-03T08:00:00",
            "end_time": "2020-04-03T09:18:00",
            "geographic_location": {
                "lat": 37.8244521,
                "lon": -122.2655363
            }
        }
    ]
}

r = requests.post('http://localhost:5000/add', json=example)
print(r.content)
