from flask import Flask, json, request
from jsonschema import validate
import time
import logging
# from shapely.geometry.point import Point
# import shapely.wkt
from openlocationcode import openlocationcode as olc
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_url_path='')
while True:
    try:
        conn = psycopg2.connect("dbname=covid19 user=covid19 port=5432\
                                 password=covid19databasepassword \
                                 host=grid-db")
        # psycopg2.extras.register_hstore(conn)
        break
    except psycopg2.OperationalError:
        logging.info("Could not connect to DB; retrying...")
        time.sleep(1)
        continue


def half_hour(ts):
    tss = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S')
    return tss - (tss - datetime.min) % timedelta(minutes=30)


def geocode(p):
    return olc.encode(float(p['lat']), float(p['lon']))


def is_pfx(pfx, code):
    """
    Returns True if pfx is a valid pluscode prefix of 'code'
    """
    pfx = normalize_olc(pfx)
    try:
        pfx_len = pfx.index('0')
        return code[:pfx_len] == pfx[:pfx_len]
    except ValueError:  # substring '0' not found
        return pfx == code


def normalize_olc(pc):
    if olc.isShort(pc):
        # normalize code 849V+ -> 849V0000+
        idx = pc.index('+')
        return pc[:idx] + '0'*(8-idx) + '+'
    return pc


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

get_schema = {
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
    if ts > datetime.utcnow():
        raise ValueError(f"Timestamp {datum['timestamp']} \
cannot be in the future")

    # ts = ts.strftime('%Y-%m-%dT%H:%M:%S')
    logging.info(">", datum)
    ts = half_hour(datum['timestamp'])
    loc = datum['location']

    # TODO: validate nonce
    # nonce = bytes.fromhex(datum['nonce'])

    with conn.cursor() as cur:
        for counter, value in datum['attributes'].items():
            cur.execute("INSERT INTO attributes(time, location,\
                        attribute, counter) VALUES (%s, %s, %s, %s)",
                        (ts, loc, counter, value))
    conn.commit()


def geocode_to_prefix(gc):
    if '0' in gc:
        idx = gc.index('0')
        return gc[:idx]+'%'
    elif '+' in gc:
        idx = gc.index('+')
        return gc[:idx]+'%'
    return gc + '%'


def do_query(query):
    # st = datetime.strptime(query['timestamp'], '%Y-%m-%dT%H:%M:%S')
    # st = st.strftime('%Y-%m-%dT%H:%M:%S')
    st = half_hour(query['timestamp'])

    geocode = query['location']
    if not olc.isValid(geocode):
        raise Exception("Invalid pluscode")
    geocode = geocode_to_prefix(geocode)
    with conn.cursor() as cur:
        cur.execute("SELECT time, attribute, sum(count)\
                    FROM grid\
                    WHERE time = %s\
                        AND location like %s\
                    GROUP BY time, attribute;", (st, geocode))
        # aggregate across location
        attrs = {}
        for row in cur:
            attrs[row[1]] = int(row[2])
        attrs['location'] = query['location']
        attrs['time'] = st
        return attrs


@app.route('/put-inc', methods=['POST'])
def add_data():
    try:
        datum = request.get_json(force=True)
        validate(datum, schema=put_inc_schema)
        if not olc.isValid(datum['location']):
            return json.jsonify({'error': 'invalid location code'}), 500
        datum['location'] = normalize_olc(datum['location'])
        logging.info(f"datum {datum}")
        insert_data(datum)
        return json.jsonify({}), 200
    except Exception as e:
        return json.jsonify({'error': str(e)}), 500


@app.route('/get', methods=['POST'])
def query_grid():
    try:
        query = request.get_json(force=True)
        validate(query, schema=get_schema)
        res = do_query(query)
        logging.info(res)
        return json.jsonify(res), 200
    except Exception as e:
        return json.jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
