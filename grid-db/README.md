# Grid DB

Data model overview [here](https://docs.google.com/document/d/1eSpYhxVbxaOs5T3LGTN00xaCVIU8OI9kGkeMLbncieA/edit)

## Getting Started

Requires:
- docker
- docker-compose
- python3

1. To run the development setup (postgres backend defined in `grid-sql/`, API backend defined in `grid-api/`), use docker-compose:

    ```
    docker-compose up
    ```

    This should bring up the Postgresql server running on port 5435 and the API server running on port 5001.

3. Test out the API:
    ```
    # if you haven't run already
    make install-python-dependencies
    # activate virtual env
    . .env/bin/activate

    # post trace data via the API
    python grid-api/post.py

    # query the grid
    python grid-api/query.py
    ```

## API Documentation

### Adding data with `PUT-INC`

`PUT-INC` pushes named counters at a place-time to the backend where they are added to existing counters. The content of a `PUT-INC` may come from a user self-reporting data or from an aggregate data source

Data posted to the API must adhere to the following JSON schema definition:

```python
put_inc_schema = {
    "type": "object",
    "required": ["timestamp", "location", "attributes"],
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},  # UTC
        "location": {"type": "string"},  # plus-code
        "attributes": {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "confirmed": {"type": "integer"},
                "symptomatic": {"type": "integer"},
                "diagnosed": {"type": "integer"}
            },
        }
    }
}
```

### Querying the Grid with `GET`

All queries adhere to the following JSON schema definition

```python
get_schema = {
    "type": "object",
    "required": ["timestamp", "location"],
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},  # UTC
        "location": {"type": "string"},  # plus-code (prefix possible)
    }
}
```

The queries may be at different levels of spatial granularity (temporal granularity under development).

---

```python
q = {
    "timestamp": "2020-04-01T00:30:00",
    "location": "849VM5FP+"
}
r = requests.post('http://localhost:5001/get', json=q)
print(r.json())
# {
#     'location': '849VM5FP+',
#     'symptomatic': 2,
#     'time': '2020-04-01T00:30:00'
# }


q = {
    "timestamp": "2020-04-01T00:30:00",
    "location": "849V0000+"
}
r = requests.post('http://localhost:5001/get', json=q)
print(r.json())
# {
#     'diagnosed': 1,
#     'symptomatic': 12,
#     'location': '849V0000+',
#     'time': '2020-04-01T00:30:00'
# }
```

---
