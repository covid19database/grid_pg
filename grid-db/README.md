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


