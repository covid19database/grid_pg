CREATE TABLE IF NOT EXISTS grid(
    time TIMESTAMP NOT NULL,
    pluscode TEXT NOT NULL,
    attributes HSTORE
);

CREATE INDEX idx_grid_attrs ON grid USING GIN(attributes);
CREATE UNIQUE INDEX IF NOT EXISTS grid_time_code_idx ON grid(time, pluscode);

CREATE TABLE IF NOT EXISTS update_log(
    time TIMESTAMP NOT NULL,
    pluscode TEXT NOT NULL,
    nonce   BYTEA NOT NULL, -- sha256 hash
    attributes HSTORE
);
CREATE UNIQUE INDEX IF NOT EXISTS update_log_uniq_nonce ON update_log(nonce);

SELECT create_hypertable('grid', 'time');
SELECT create_hypertable('update_log', 'time');


CREATE FUNCTION update_grid() 
RETURNS INTEGER 
TRANSFORM FOR TYPE hstore
AS $$
res = plpy.execute("SELECT half_hour(time) as hh, pluscode, attributes FROM update_log ORDER BY hh, pluscode")
if len(res) == 0:
    return 0
first = res[0]
key = (first["hh"], first["pluscode"])
attrs = first["attributes"]
num = 0

def merge(key, original, new):
    if key == "feels_sick":
        oval = original == 'True'
        nval = new == 'True'
        return str(nval or oval)
        
for row in res[1:]:
    pass
    newkey = (row["hh"], row["pluscode"])
    if newkey == key:
        for k,v in row["attributes"].items():
            if k in attrs:
                attrs[k] = merge(k, attrs[k], v)
            else:
                attrs[k] = v
    else:
        stmt = plpy.prepare("INSERT INTO grid(time, pluscode, attributes) VALUES\
                            ($1, $2, $3) ON CONFLICT DO NOTHING", ["timestamp", "varchar", "hstore"])
        plpy.execute(stmt, [key[0], key[1], attrs])
        num += 1
        attrs = row["attributes"]
        key = (row["hh"], row["pluscode"])
stmt = plpy.prepare("INSERT INTO grid(time, pluscode, attributes) VALUES\
                    ($1, $2, $3) ON CONFLICT DO NOTHING", ["timestamp", "varchar", "hstore"])
plpy.execute(stmt, [key[0], key[1], attrs])
num += 1
return num
$$ LANGUAGE plpython3u;

CREATE FUNCTION update_grid_from_log() RETURNS trigger AS $$
row = TD["row"]
stmt = plpy.prepare("INSERT INTO grid(time, pluscode) VALUES\
                    ($1, $2, $3)", ["timestamp", "varchar"])
plpy.execute(stmt, [row["time"], row["pluscode"]])
return "OK"
return

stmt = plpy.prepare("SELECT attributes FROM grid\
                    WHERE grid.time = half_hour($1) AND\
                    grid.pluscode = $2", ["varchar", "varchar"])
res = plpy.execute(stmt, [row["time"], row["pluscode"]])
if len(res) == 0:
    grid_attrs = {
        "feels_sick": row["attributes"].get("feels_sick", False)
    }
    stmt = plpy.prepare("INSERT INTO grid(time, pluscode, attributes) VALUES\
                        ($1, $2, $3, $4)", ["timestamp", "varchar", "varchar", "hstore"])
    plpy.execute(stmt, [row["time"], row["pluscode"], grid_attrs])
else:
    rec = next(res)
return
$$ LANGUAGE plpython3u;

CREATE TRIGGER check_update
    BEFORE UPDATE ON update_log
    FOR EACH ROW
    EXECUTE FUNCTION update_grid_from_log();
