import json
import psycopg2
import geopandas as gp
import shapely
from psycopg2.extras import execute_values
from shapely.geometry import Polygon

doc = json.load(open('data/alameda-parcels.geojson'))
columns = [col['name'] for col in doc['meta']['view']['columns']]

data = map(lambda x: dict(zip(columns, x)), doc['data'])

conn = psycopg2.connect("dbname=covid19 user=covid19\
                         password=covid19databasepassword host=localhost")

def bbox_to_poly(poly):
    (xmin, ymin, xmax, ymax) = poly.bounds
    # TODO: add margins?
    xmin -= 1e-5
    ymin -= 1e-5
    xmax += 1e-5
    ymax += 1e-5
    return Polygon([[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin]])

df = gp.GeoDataFrame.from_records(data)
df.loc[:, 'geometry'] = df['the_geom'].apply(shapely.wkt.loads)
df.loc[:, 'geometry'] = df['geometry'].apply(lambda x: bbox_to_poly(x))
#0/0
# df.loc[:, 'geometry'] = df['geometry'].apply(lambda x: x.centroid)
df.loc[:, 'geometry'] = df['geometry'].apply(shapely.wkt.dumps)


def get_rows():
    for (rowid, row) in df.iterrows():
        # yield ("Alameda", f"AL-{row['id']}", geo)
        #if type(row['geometry']) != Polygon:
        #    continue
        geo = f"SRID=4326;{row['geometry']}"
        # print(geo)
        yield ("Alameda", row['APN'], geo)


with conn.cursor() as cur:
    execute_values(cur, "INSERT INTO\
        parcel_geometry(source, apn, shape)\
        VALUES %s", get_rows())
    conn.commit()
