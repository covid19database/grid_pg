CREATE TABLE IF NOT EXISTS location_history(
    userid  INT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    geographic_location geography(POINT, 4326),
    semantic_location TEXT,
    address TEXT
);
-- CREATE INDEX IF NOT EXISTS geoloc_idx ON location_history(geographic_location);
CREATE INDEX IF NOT EXISTS geoloc_idx ON location_history USING  GIST (geographic_location);

CREATE TABLE IF NOT EXISTS parcel_geometry(
    source TEXT NOT NULL,
    apn TEXT NOT NULL,
    shape geography(POLYGON, 4326) NOT NULL
);
-- CREATE INDEX IF NOT EXISTS shape_idx ON parcel_geometry(shape);
CREATE INDEX IF NOT EXISTS shape_idx ON parcel_geometry USING GIST (shape);
CREATE INDEX IF NOT EXISTS parcel_apn_idx ON parcel_geometry(apn);

CREATE TABLE IF NOT EXISTS parcels(
    apn TEXT NOT NULL,
    address TEXT,
    zipcode TEXT,
    type TEXT,
    city TEXT
);

CREATE INDEX IF NOT EXISTS apn_idx ON parcels(apn);

CREATE OR REPLACE VIEW semantic_parcels AS
SELECT parcels.apn,
       parcels.address,
       parcels.zipcode,
       parcels.type,
       parcels.city,
       parcel_geometry.source,
       parcel_geometry.shape
FROM parcels
JOIN parcel_geometry ON parcels.apn = parcel_geometry.apn;

CREATE TABLE IF NOT EXISTS sick(
    userid INT NOT NULL,
    time TIMESTAMP NOT NULL,
    feels_sick INT NOT NULL
);

CREATE TABLE IF NOT EXISTS interactions(
    userid_a INT NOT NULL,
    userid_b INT NOT NULL,
    time TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS grid(
    time TIMESTAMP NOT NULL,
    pluscode TEXT NOT NULL,
    domain TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS grid_time_code_idx ON grid(time, pluscode);
CREATE INDEX IF NOT EXISTS domain_idx ON grid(domain);

CREATE TABLE IF NOT EXISTS facts(
    domain TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS fact_domain_idx ON facts(domain);


CREATE OR REPLACE FUNCTION plus_code(poly TEXT) RETURNS TEXT AS $$
import sys
import re
sys.path.append('/home/gabe/src/covid/pg/.env/lib/python3.7/site-packages')
from openlocationcode import openlocationcode as olc
x, y = re.findall(r'(-?[0-9]+.?[0-9]*)',poly)
x = float(x)
y = float(y)
return olc.encode(y, x)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION half_hour(ts TIMESTAMP) RETURNS TIMESTAMP AS $$
from datetime import datetime, timedelta
tss = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
return tss - (tss - datetime.min) % timedelta(minutes=30)
$$ LANGUAGE plpython3u;


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

CREATE OR REPLACE VIEW grid_count AS
SELECT count(distinct userid) as num,
       plus_code(st_astext(geographic_location)) as geocode,
       half_hour(start_time) as timestamp
FROM location_history
group by geocode, timestamp
ORDER BY timestamp asc;

CREATE OR REPLACE VIEW grid_sick AS
SELECT
       count(distinct lh.userid) as num_sick,
       plus_code(st_astext(geographic_location)) as geocode,
       half_hour(start_time) as timestamp
FROM location_history as lh
JOIN sick_continuous as sc on lh.userid = sc.userid and half_hour(start_time) = sc.timestamp
group by geocode, half_hour(start_time)
ORDER BY timestamp asc;

SELECT create_hypertable('sick', 'time');
SELECT create_hypertable('grid', 'time');
