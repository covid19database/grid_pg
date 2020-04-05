import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

df = pd.read_csv('data/alameda-address.csv')
df = df[['APN_1', 'ADDRESS', 'ZIPCODE', 'AddressTyp', 'CITY']]

conn = psycopg2.connect("dbname=covid19 user=covid19\
                         password=covid19databasepassword host=localhost")


def get_rows():
    for (rowid, row) in df.iterrows():
        # convert to multipolygon
        yield row


with conn.cursor() as cur:
    execute_values(cur, "INSERT INTO\
        parcels(apn, address, zipcode, type, city)\
        VALUES %s", get_rows())
    conn.commit()
