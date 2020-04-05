import psycopg2
from psycopg2.extras import execute_values
import json
from datetime import datetime, timedelta

import sys


if len(sys.argv) < 3:
    print("Usage: python load_takeout.py <userid> <Location History.json>")
    sys.exit(1)
userid, location_file = sys.argv[1], sys.argv[2]
print(f"Loading {location_file} data for userid {userid}")

conn = psycopg2.connect("dbname=covid19 user=postgres\
                         password=covid19 host=localhost")

location_data = json.load(open(location_file))
if 'locations' not in location_data:
    print("Malformed file")
    sys.exit(1)

low_watermark = datetime(2020, 1, 1)

# TODO: JSON schema?
values = []
for loc in location_data['locations']:
    timestampMs = int(loc['timestampMs']) / 1000  # to seconds
    ts = datetime.utcfromtimestamp(timestampMs)
    if ts <= low_watermark:
        continue
    start_time = ts.strftime('%Y-%m-%dT%H:%M:%S')
    end_time = (ts + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S')
    lat = int(loc['latitudeE7']) / 1e7
    lon = int(loc['longitudeE7']) / 1e7
    coord = f'SRID=4326;POINT({lon} {lat})'
    values.append(
        (userid, start_time, end_time, coord)
    )
with conn.cursor() as cur:
    execute_values(cur, "INSERT INTO\
        location_history(userid, start_time, end_time, geographic_location)\
        VALUES %s", values)
    conn.commit()
