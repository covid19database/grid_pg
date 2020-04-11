from flask import Flask, json, request
from datetime import datetime
from jsonschema import validate
import logging
# from shapely.geometry.point import Point
# import shapely.wkt
from openlocationcode import openlocationcode as olc
import psycopg2
import psycopg2.extras
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_url_path='')
conn = psycopg2.connect("dbname=covid19 user=covid19 port=5432\
                         password=covid19databasepassword host=db")
psycopg2.extras.register_hstore(conn)


add_data_schema = {
    "type": "object",
    "required": ["nonce", "timestamp", "location", "attributes"],
    "properties": {
        "nonce": {"type": "string"},  # hex-encoded SHA256
        "timestamp": {"type": "string", "format": "date-time"},  # UTC
        "location": {"type": "string"},  # plus-code
        "attributes": {
            "type": "object",
            "properties": {
                "feels_sick": {"type": "boolean"},
                "age": {"type": "integer"},
            },
        }
    }
}

query_grid_schema = {
    "type": "object",
    "required": ["timestamp", "location"],
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},  # UTC
        "location": {"type": "string"},  # plus-code (prefix possible)
    }
}


def insert_data(datum):
    # parse/validate timestamp
    ts = datetime.strptime(datum['timestamp'], '%Y-%m-%dT%H:%M:%S')
    ts = ts.strftime('%Y-%m-%dT%H:%M:%S')

    nonce = bytes.fromhex(datum['nonce'])
    attrs = {k: str(v) for k,v in datum['attributes'].items()}

    with conn.cursor() as cur:
        cur.execute("INSERT INTO update_log(time, pluscode, nonce, attributes)\
                    VALUES(%s, %s, %s, %s)",
                    (ts, datum['location'], nonce, attrs))
        conn.commit()


def geocode(p):
    return olc.encode(float(p['lat']), float(p['lon']))


def do_query(query):
    st = datetime.strptime(query['timestamp'], '%Y-%m-%dT%H:%M:%S')
    st = st.strftime('%Y-%m-%dT%H:%M:%S')

    geocode = query['location']
    if len(geocode) % 2 != 0:
        raise Exception("Geocode must be of length 2, 4, 6 or 8")
    if len(geocode) < 8:
        pass
    else:
        geocode += "+"
        # select substring(pluscode from 0 for 9) as ss, count(*) from grid group by ss;
    with conn.cursor() as cur:
        print(cur.mogrify("SELECT time, pluscode, attributes FROM grid WHERE\
                     time = half_hour(%s::timestamp) AND\
                     pluscode = %s", (st, geocode)))
        cur.execute("SELECT time, pluscode, attributes FROM grid WHERE\
                     time = half_hour(%s::timestamp) AND\
                     pluscode = %s", (st, geocode))
        res = cur.fetchone()
        if res is None:
            return {}
        print(res)
        attrs = res[2]
        attrs['time'] = res[0]
        return attrs


@app.route('/add', methods=['POST'])
def add_data():
    try:
        datum = request.get_json(force=True)
        validate(datum, schema=add_data_schema)
        insert_data(datum)
        return json.jsonify({}), 200
    except Exception as e:
        return json.jsonify({'error': str(e)}), 500


@app.route('/query', methods=['POST'])
def query_grid():
    try:
        query = request.get_json(force=True)
        validate(query, schema=query_grid_schema)
        return json.jsonify(do_query(query)), 200
    except Exception as e:
        return json.jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
