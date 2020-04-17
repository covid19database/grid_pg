CREATE TABLE IF NOT EXISTS attributes(
    grid_time   TIMESTAMP NOT NULL,
    grid_loc    TEXT      NOT NULL,
    attribute   TEXT      NOT NULL,
    counter     INTEGER   NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE VIEW grid AS
    SELECT grid_time as time,
           grid_loc as location,
           attribute,
           sum(counter) as count
    FROM attributes
    GROUP BY time, location, attribute
    ORDER BY time ASC;

CREATE OR REPLACE FUNCTION plus_code(poly TEXT) RETURNS TEXT AS $$
import sys
import re
sys.path.append('/var/lib/postgresql/.local/lib/python3.7/site-packages')
from openlocationcode import openlocationcode as olc
x, y = re.findall(r'(-?[0-9]+.?[0-9]*)',poly)
x = float(x)
y = float(y)
return olc.encode(y, x)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION is_prefix(pfx TEXT, pluscode TEXT) RETURNS BOOLEAN AS $$
import sys
sys.path.append('/var/lib/postgresql/.local/lib/python3.7/site-packages')
from openlocationcode import openlocationcode as olc
try:
    pfx_len = pfx.index('0')
    return pluscode[:pfx_len] == pfx[:pfx_len]
except ValueError:  # substring '0' not found
    return pfx == pluscode
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION half_hour(ts TIMESTAMP) RETURNS TIMESTAMP AS $$
from datetime import datetime, timedelta
tss = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
return tss - (tss - datetime.min) % timedelta(minutes=30)
$$ LANGUAGE plpython3u;
