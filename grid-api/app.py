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
        psycopg2.extras.register_hstore(conn)
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
    # ts = datetime.strptime(datum['timestamp'], '%Y-%m-%dT%H:%M:%S')
    # ts = ts.strftime('%Y-%m-%dT%H:%M:%S')
    ts = half_hour(datum['timestamp'])
    loc = datum['location']

    nonce = bytes.fromhex(datum['nonce'])

    # TODO: check if it is in the log yet?

    with conn.cursor() as cur:
        strattrs = {k: str(v) for k, v in datum['attributes'].items()}
        cur.execute("INSERT INTO update_log(time, pluscode, nonce, attributes)\
                     VALUES (%s, %s, %s, %s)", (ts, loc, nonce, strattrs))
    conn.commit()

    attrs = {k: 1 if v else 0 for k, v in datum['attributes'].items()}

    # merge into the grid
    with conn.cursor() as cur:
        cur.execute("SELECT attributes FROM grid \
                     WHERE \
                        time = %s \
                        AND pluscode = %s", (ts, datum['location']))
        grid = cur.fetchone()
        if grid is None:
            # create new grid square
            q = "INSERT INTO grid(time, pluscode, attributes)\
                 VALUES (%s, %s, %s)"
            for k, v in attrs.items():
                attrs[k] = str(v)
            attrs['count'] = str(1)
            cur.execute(q, (ts, datum['location'], attrs))
        else:
            # update existing grid
            grid = grid[0]
            count = int(grid['count'])
            grid['count'] = str(count + 1)
            for k, v in attrs.items():
                newv = int(grid.get(k, '0')) + v
                grid[k] = str(newv)
            q = "UPDATE grid SET attributes = %s \
                 WHERE time = %s AND pluscode = %s"
            cur.execute(q, (grid, ts, datum['location']))
    conn.commit()


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
        if not olc.isValid(datum['location']):
            return json.jsonify({'error': 'invalid location code'})
        if olc.isShort(datum['location']):
            # normalize code 849V+ -> 849V0000+
            idx = datum['location'].index('+')
            code = datum['location'][:idx] + '0'*(8-idx) + '+'
            datum['location'] = code
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
        return json.jsonify({'error': e}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
