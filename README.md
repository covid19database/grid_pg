# Schema Overview

Following notes on [this doc](https://docs.google.com/document/d/1AfhYHz5W0eV_eDM_5DSzx7uOJRod5VG8neBqYxNqo1w/edit#heading=h.gs1z8jfan3o9)

## Temporal Grid Schema

The temporal grid schema divides space-time into 30-minute chunks of 14m-14m space. Timestamps are aligned to the hour and half-hour and are stored in UTC time. The 14m-14m grid is represented by a full [plus code](https://plus.codes/) stored as text. I refer to the unique tuple of 30-min aligned timestamp and pluscode a **place-time**.

A domain is currently the SHA-256 hash of the timestamp and plus code; it is intended as the foreign key for external lookups (Note: _my impression of the domain was unclear from the API document. I'm not really using it at the moment, so let me know how I can make it work better for you_).

The current implementation of the grid is a sparse representation.

```sql
CREATE TABLE IF NOT EXISTS grid(
    time TIMESTAMP NOT NULL,
    pluscode TEXT NOT NULL,
    domain TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS grid_time_code_idx ON grid(time, pluscode);
CREATE INDEX IF NOT EXISTS domain_idx ON grid(domain);
```

The grid is supported by two UDFs:

- `plus_code(wkt_text)` accepts WKT-formatted strings of geographic points and returns a full plus-code:
    ```sql
    select start_time, plus_code(st_astext(geographic_location)) from location_history;

    -- +---------------------+-------------+
    -- | start_time          | plus_code   |
    -- |---------------------+-------------|
    -- | 2020-04-03 22:36:13 | 849VRPXM+JQ |
    -- | 2020-04-03 23:24:00 | 849VVP2M+5J |
    -- | 2020-04-03 23:31:52 | 849VVP2M+CV |
    ```

- `half_hour(timestamp)` accepts `YYYY-MM-DD HH:MM:SS` formatted timestamps and returns the timestamp aligned to the nearest _previous_ half hour.

    ```sql
    select half_hour(start_time), plus_code(st_astext(geographic_location)) from location_history;

    -- +---------------------+-------------+
    -- | start_time          | plus_code   |
    -- |---------------------+-------------|
    -- | 2020-04-03 22:30:00 | 849VRPXM+JQ |
    -- | 2020-04-03 23:00:00 | 849VVP2M+5J |
    -- | 2020-04-03 23:30:00 | 849VVP2M+CV |
    ```

### Storing People Counts in the Grid

Because I'm not sure of how I want to handle arbitrary key-value pairs at each grid square, I'm currently defining
two views:

- `grid_count`: stores the number of unique location records at each place-time:
    ```sql
    CREATE OR REPLACE VIEW grid_count AS
    SELECT count(distinct userid) as num,
           plus_code(st_astext(geographic_location)) as geocode,
           half_hour(start_time) as timestamp
    FROM location_history
    group by geocode, timestamp
    ORDER BY timestamp asc;

    select * from grid_count limit 10;
    -- +------+-------------+---------------------+
    -- | num  | geocode     | timestamp           |
    -- |------+-------------+---------------------|
    -- | 2    | 849VVP2M+9W | 2020-04-02 00:00:00 |
    -- | 1    | 849VVP2M+9W | 2020-04-02 00:30:00 |
    -- | 1    | 849VVP2M+9W | 2020-04-02 01:00:00 |
    -- | 1    | 849VVP2M+9W | 2020-04-02 01:30:00 |
    -- | 1    | 849VVP2M+9V | 2020-04-02 02:00:00 |
    -- | 1    | 849VVP2M+9W | 2020-04-02 02:00:00 |
    -- | 1    | 849VVP2M+9V | 2020-04-02 02:30:00 |
    -- | 1    | 849VVP2M+9W | 2020-04-02 02:30:00 |
    -- | 1    | 849VVP2M+9W | 2020-04-02 03:00:00 |
    -- | 1    | 849VVP2M+9W | 2020-04-02 03:30:00 |
    -- +------+-------------+---------------------+
    ```

- `grid_sick`: stores the number of unique location records at each place-time that correspond to users who have self-identified as "feeling sick":

    ```sql
    CREATE OR REPLACE VIEW grid_sick AS
    SELECT
           count(distinct lh.userid) as num_sick,
           plus_code(st_astext(geographic_location)) as geocode,
           half_hour(start_time) as timestamp
    FROM location_history as lh
    JOIN sick_continuous as sc on lh.userid = sc.userid and half_hour(start_time) = sc.timestamp
    group by geocode, half_hour(start_time)
    ORDER BY timestamp asc;

    select * from grid_sick limit 10;
    -- +------------+-------------+---------------------+
    -- | num_sick   | geocode     | timestamp           |
    -- |------------+-------------+---------------------|
    -- | 1          | 849VVP2M+9W | 2020-04-02 00:00:00 |
    -- | 1          | 849VVP2M+9W | 2020-04-03 00:00:00 |
    -- | 1          | 849VVP2M+9W | 2020-04-03 01:00:00 |
    -- | 1          | 849VVP2M+9W | 2020-04-03 01:30:00 |
    -- | 1          | 849VVP2M+CW | 2020-04-03 01:30:00 |
    -- | 1          | 849VVP2M+9W | 2020-04-03 02:00:00 |
    -- | 1          | 849VVP2M+9W | 2020-04-03 02:30:00 |
    -- | 1          | 849VVP2M+9V | 2020-04-03 03:00:00 |
    -- | 1          | 849VVP2M+9W | 2020-04-03 03:00:00 |
    -- | 1          | 849VVP2M+9V | 2020-04-03 03:30:00 |
    -- +------------+-------------+---------------------+
    ```

## Supporting Data Schemas

The above grid schema exists independent of any individual data sources. The two views defined above take advantage of a supporting schema that captures individual location history traces, self-reporting on feeling sick and other municipal data sources.

### Location History

Individual location histories can be captured by the following schema

```sql
CREATE TABLE IF NOT EXISTS location_history(
    userid  INT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    geographic_location geography(POINT, 4326),
    semantic_location TEXT,
    address TEXT
);
CREATE INDEX IF NOT EXISTS geoloc_idx ON location_history USING GIST (geographic_location);
```

- `userid`: a unique identifier to tie a location history to a sickness reporting (see `sick` table schema below)
- `start_time`, `end_time`: store the UTC range of time that a user was at a given location
- `geographic_location`: a geographic `POINT` indicating a user's location
- `semantic_location`: the semantic name of the user's location (e.g. "Berkeley Bowl")
- `address`: the street address of the user's location (e.g. "1960 Adeline St, Oakland, CA 94607")

It is expected that *at least one* of `geographic_location`, `semantic_location` and `address` is populated.

### Sickness Reporting

The `sick` table captures reports of sickness over time. Through a survey or other means, a user (identified by `userid`) reports that they feel sick (`feels_sick = 1`) or not (`feels_sick = 0`) at a given time (likely specified at the granularity of a day).

The `sick_continuous` view takes advantage of TimescaleDB's aggregation API to carry a report of being sick or not forward through time so it is easier to join against (see examples at the end of the SQL snippet below):

```sql
CREATE TABLE IF NOT EXISTS sick(
    userid INT NOT NULL,
    time TIMESTAMP NOT NULL,
    feels_sick INT NOT NULL
);

SELECT create_hypertable('sick', 'time');

CREATE OR REPLACE VIEW sick_continuous AS
SELECT timestamp, userid, COALESCE(locf, 0) as feels_sick FROM
(
    SELECT
        time_bucket_gapfill('30 minute', time, '2020-01-01 00:00:00'::timestamp, now()) as timestamp,
        userid,
        max(feels_sick) as feels_sick,
        locf(max(feels_sick)) as locf
    FROM sick
    GROUP BY timestamp, userid
) a
WHERE a.locf IS NOT NULL
ORDER BY timestamp ASC;

-- raw "sick" reports
select * from sick;
+----------+---------------------+--------------+
| userid   | time                | feels_sick   |
|----------+---------------------+--------------|
| 1        | 2020-04-02 00:00:00 | 0            |
| 1        | 2020-04-03 00:00:00 | 1            |
| 2        | 2020-04-03 00:00:00 | 1            |
+----------+---------------------+--------------+

-- made continuous
+------------------------+----------+--------------+
| timestamp              | userid   | feels_sick   |
|------------------------+----------+--------------|
| 2020-04-02 21:30:00-04 | 1        | 0            |
| 2020-04-02 22:00:00-04 | 1        | 0            |
| 2020-04-02 22:30:00-04 | 1        | 0            |
| 2020-04-02 23:00:00-04 | 1        | 0            |
| 2020-04-02 23:30:00-04 | 1        | 0            |
| 2020-04-03 00:00:00-04 | 2        | 1            |
| 2020-04-03 00:00:00-04 | 1        | 1            |
| 2020-04-03 00:30:00-04 | 2        | 1            |
| 2020-04-03 00:30:00-04 | 1        | 1            |
| 2020-04-03 01:00:00-04 | 1        | 1            |
| 2020-04-03 01:00:00-04 | 2        | 1            |
| 2020-04-03 01:30:00-04 | 2        | 1            |
| 2020-04-03 01:30:00-04 | 1        | 1            |
| 2020-04-03 02:00:00-04 | 1        | 1            |
```

### Geographic Context

I've done some work integrating parcel data from Alameda county which allows us to map the following

```
parcel # (APN)  <---->  geographic bounding box <---> user geographic coordinates
    ^
    |
    |
    v
street address
```

I can document this later if we need; data files available for download [here](http://files.gtf.fyi/alameda-county-parcel-address.tar.gz) (via Alameda county data hub)

## Data Ingestion

### API

`api/app.py` implements a simple Flask application that supports:
- pushing data to the server: location tracing and sickness reporting
    - example: **`api/post.py`**
- simple grid queries: count of people (sick, or total) in a placetime
    - example: **`api/query.py`**

**TODO: dockerize the API server**

### Bulk Data Load

Following scrips have been written:
- `load_kml.py`: loads a KML export from Google timeline into the `location_history` table
- `load_takeout.py`: loads a GeoJSON export from Google takeout into the `location_history` table
- `load-alameda-geo.py`: loads in Alameda county shape files
- `load_alameda_address.py`: loads in Alameda county address records (ties APNs to street addresses)

## Data Formats

### Google Timeline KML Export

**Sample file**: `data/history-2020-04-01.kml`

To download:
1. Navigate to [maps.google.com](http://maps.google.com/)
2. Use the menu to navigate to "Your timeline"
3. Pick the day you want, add places or export your location history (if you do not have location history enabled, you should be able to add a sequence of places)
4. Use the "gear icon" in the lower right corner and select the option "Export this day to KML"


# Dev Setup

Dockerfile located in `docker/`; creates a single Postgresql-11 server with postgis, timescaledb and plpython3u extensions. **Note: exposed on port `5434` (non-standard) to avoid conflicting with existing postgresql installations**

Requires:
- docker
- python3

To run the postgresql server:
- `make run`
- runs in the foreground and deletes the database on exit

Load in the parcel data:
- `make install-python-dependencies`
- `make load-data`

Load in sample location history data:
- `python scripts/load_kml.py 1 data/history-2020-04-01.kml`

### Setup/Install (non-docker)

- relies on Postgresql 11 (as of now)
- PostGIS:
    - install: `sudo apt install postgresql-11-postgis-3`
    - SQL: `CREATE EXTENSION postgis;`
- PLpython3:
    - install: `sudo apt install postgresql-plpython3-11`
    - SQL: `CREATE EXTENSION plpython3u;`
- Timescaledb:
    - install: look at website
    - SQL: `CREATE EXTENSION timescaledb CASCADE;`

- `setup.sql` defines all tables, functions, etc:
    - remember to change relative import paths in the `half_hour` and `plus_code` UDFs
