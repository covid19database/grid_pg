import psycopg2
from psycopg2.extras import execute_values
import fastkml as fk
import shapely.wkt
from shapely.geometry.point import Point

import sys


if len(sys.argv) < 3:
    print("Usage: python load_takeout.py <userid> <Location History.json>")
    sys.exit(1)
userid, location_file = sys.argv[1], sys.argv[2]
print(f"Loading {location_file} data for userid {userid}")

conn = psycopg2.connect("dbname=covid19 user=covid19 port=5434\
                         password=covid19databasepassword host=localhost")
k = fk.KML()
k.from_string(open(location_file).read())
doc = list(k.features())[0]
values = []
cur = conn.cursor()
for point in doc.features():
    if type(point.geometry) != shapely.geometry.point.Point:
        continue
    start = point.begin.strftime('%Y-%m-%dT%H:%M:%S')
    end = point.end.strftime('%Y-%m-%dT%H:%M:%S')
    print(point.address,
         '|',
          point.name,
         '|',
          point.begin.strftime('%Y-%m-%dT%H:%M:%S'),
          point.end.strftime('%Y-%m-%dT%H:%M:%S'),
          point.geometry)
    geopoint = Point(point.geometry.x, point.geometry.y)
    geo = shapely.wkt.dumps(geopoint)
    geopoint = f"SRID=4326;{geo}"
    #values.append(
    value = (userid, start, end, geopoint, point.name, point.address)
    #)
    cur.execute("INSERT INTO\
        location_history(userid, start_time, end_time, \
        geographic_location, semantic_location, address) \
        VALUES %s", [value])
conn.commit()
