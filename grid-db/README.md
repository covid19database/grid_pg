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

### Posting data

User data posted to the API must adhere to the following JSON schema definition:

```python
add_data_schema = {
    "type": "object",
    "required": ["nonce", "timestamp", "location", "attributes"],
    "properties": {
        "nonce": {"type": "string"},  # hex-encoded SHA256
        "timestamp": {"type": "string", "format": "date-time"},  # UTC
        "location": {"type": "string"},  # plus-code
        "attributes": {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "symptom_coughing": {"type": "boolean"},
                "symptom_sore_throat": {"type": "boolean"},
                "infected_tested": {"type": "boolean"},
                "had_mask": {"type": "boolean"},
                "had_gloves": {"type": "boolean"},
            },
        }
    }
}
```

Note that the supported properties are **all boolean**. The server tracks the
number of "True" responses for each property, as well as the total number of
responses, for each placetime.

**TODO:** need to generate/sign nonces in a way that preserves the properties outlined in the document above

### Querying the Grid

All queries adhere to the following JSON schema definition

```python
query_grid_schema = {
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
    "timestamp": "2020-04-05T11:30:00",
    "location": "849VVP2J+"
}
r = requests.post('http://localhost:5001/query', json=q)
print(r.json())
# {
#     'count': 2,
#     'had_gloves': 0,
#     'had_mask': 2,
#     'infected_tested': 0,
#     'symptom_coughing': 1,
#     'symptom_sore_throat': 0,
#     'location': '849VVP2J+',
#     'time': '2020-04-05T11:30:00'
# }


q = {
    "timestamp": "2020-04-05T11:30:00",
    "location": "849V0000+"
}
r = requests.post('http://localhost:5001/query', json=q)
print(r.json())
# {
#     'count': 33,
#     'had_gloves': 9,
#     'had_mask': 14,
#     'infected_tested': 3,
#     'symptom_coughing': 3,
#     'symptom_sore_throat': 3,
#     'location': '849V0000+',
#     'time': '2020-04-05T11:30:00'
# }
```

---
