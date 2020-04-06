from flask import Flask, json, request
from datetime import datetime
from jsonschema import validate
import logging
from shapely.geometry.point import Point
import shapely.wkt
from openlocationcode import openlocationcode as olc
import psycopg2
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_url_path='')
conn = psycopg2.connect("dbname=covid19 user=covid19 port=5434\
                         password=covid19databasepassword host=localhost")


add_data_schema = {
    "type": "object",
    "required": ["userid", "timestamp", "feels_sick"],
    "properties": {
        "userid": {"type": "integer"},
        "timestamp": {"type": "string", "format": "date-time"},  # UTC
        "feels_sick": {"type": "boolean"},
        "location_trace": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start_time": {"type": "string", "format": "date-time"},
                    "end_time": {"type": "string", "format": "date-time"},
                    "geographic_location": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lon": {"type": "number"},
                        },
                    },
                    "semantic_location": {"type": "string"},
                    "address": {"type": "string"},
                }
            }
        }
    }
}

query_grid_schema = {
    "type": "object",
    "required": ["start_time", "end_time"],
    "properties": {
        "start_time": {"type": "string", "format": "date-time"},
        "end_time": {"type": "string", "format": "date-time"},
        "pluscodes": {"type": "array", "items": {"type": "string"}},
        "coordinates": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lon": {"type": "number"}
            }
        }},
        "feels_sick_only": {"type": "boolean"}
    }
}


def insert_data(datum):
    ts = datetime.strptime(datum['timestamp'], '%Y-%m-%dT%H:%M:%S')
    ts = ts.strftime('%Y-%m-%dT%H:%M:%S')
    with conn.cursor() as cur:
        feels_sick = 1 if datum['feels_sick'] else 0
        cur.execute("INSERT INTO sick(userid, time, feels_sick)\
                     VALUES (%s, %s, %s)",
                    (datum['userid'], ts, feels_sick))
        for loc in datum['location_trace']:
            st = datetime.strptime(loc['start_time'], '%Y-%m-%dT%H:%M:%S')
            st = st.strftime('%Y-%m-%dT%H:%M:%S')
            et = datetime.strptime(loc['end_time'], '%Y-%m-%dT%H:%M:%S')
            et = et.strftime('%Y-%m-%dT%H:%M:%S')
            if 'geographic_location' in loc:
                lat = loc['geographic_location']['lat']
                lon = loc['geographic_location']['lon']
                p = shapely.wkt.dumps(Point(lon, lat))
                value = (datum['userid'], st, et, p)
                cur.execute("INSERT INTO \
                             location_history(userid, start_time, end_time,\
                              geographic_location)\
                             VALUES (%s, %s, %s, %s)", value)
            elif 'semantic_location' in loc:
                value = (datum['userid'], st, et, loc['semantic_location'])
                cur.execute("INSERT INTO \
                             location_history(userid, start_time, end_time,\
                              semantic_location)\
                             VALUES (%s, %s, %s, %s)", value)
            elif 'address' in loc:
                value = (datum['userid'], st, et, loc['address'])
                cur.execute("INSERT INTO \
                             location_history(userid, start_time, end_time,\
                              address)\
                             VALUES (%s, %s, %s, %s)", value)
        conn.commit()


def geocode(p):
    return olc.encode(float(p['lat']), float(p['lon']))


def do_query(query):
    st = datetime.strptime(query['start_time'], '%Y-%m-%dT%H:%M:%S')
    st = st.strftime('%Y-%m-%dT%H:%M:%S')
    et = datetime.strptime(query['end_time'], '%Y-%m-%dT%H:%M:%S')
    et = et.strftime('%Y-%m-%dT%H:%M:%S')

    geocodes = query.get('geocodes')
    if geocodes is None:
        geocodes = [geocode(p) for p in query.get('coordinates', [])]
    if len(geocodes) == 0:
        raise Exception("Needs non-zero-length geocodes or coordinates")
    # need to make a 'tuple' for psycopg2
    geocodes = tuple(geocodes)

    with conn.cursor() as cur:
        if query.get('feels_sick_only', False):
            cur.execute("SELECT num_sick, geocode, timestamp FROM grid_sick\
                         WHERE timestamp >= %s AND timestamp <= %s\
                         AND geocode IN (%s)", (st, et, geocodes))
        else:
            cur.execute("SELECT num, geocode, timestamp FROM grid_count\
                         WHERE timestamp >= %s AND timestamp <= %s\
                         AND geocode IN %s", (st, et, geocodes))
        for row in cur:
            yield {'num': row[0], 'geocode': row[1], 'timestamp': row[2]}


@app.route('/add', methods=['POST'])
def add_data():
    try:
        datum = request.get_json(force=True)
        validate(datum, schema=add_data_schema)
        insert_data(datum)
        return json.jsonify({}), 200
    except Exception as e:
        return json.jsonify({'error': str(e)}), 500


@app.route('/grid', methods=['POST'])
def query_grid():
    try:
        query = request.get_json(force=True)
        validate(query, schema=query_grid_schema)
        rows = list(do_query(query))
        return json.jsonify(rows), 200
    except Exception as e:
        return json.jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
