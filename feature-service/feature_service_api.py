# ./feature_service_api.py

from flask import Flask, jsonify
from datetime import date, timezone
import os
import psycopg2
from psycopg2.extras import RealDictCursor

from gridstatus import CAISO, Ercot, PJM, NYISO, ISONE, MISO, SPP

app = Flask(__name__)

# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql://user:<@RQfmoJu8f?5$(E@34.60.16.16:5432/feature-service-db"
# )

DB_HOST = os.getenv("DB_HOST", "34.60.16.16")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "feature-service-db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "%,f_KA}i@e1KX0`(")

## Public Connection
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pzQNLo8m$cULtO3c@34.60.16.16:5432/feature-service-db'
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

## Initialize Cloud SQL Connection
# app.config["SQLALCHEMY_DATABASE_URI"] = (
#     "postgresql+psycopg2://{user}:{pwd}@/{db}"
#     "?host=/cloudsql/{instance}"
# ).format(
#     user="user",
#     pwd="pzQNLo8m$cULtO3c",
#     db="feature-service-db",
#     instance="timeseries-energy-forecasting:us-central1:timeseries-energy-forecasting-instance"  # project:region:instance
# )

## Initialize Logging Configuration
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
# )

# logger = logging.getLogger()

ISO_MAP = {
    "caiso": CAISO,
    "ercot": Ercot,
    "pjm": PJM,
    "nyiso": NYISO,
    "isone": ISONE,
    "miso": MISO,
    "spp": SPP,
}


def pick(row, names):
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return None


def to_utc(value):
    if value is None:
        return None

    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)

# def get_db_connection():
#     return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )

def insert_energy_timeseries(record):
    sql = """
        INSERT INTO energy_timeseries (
            iso_code,
            interval_start_utc,
            interval_end_utc,
            load_mw,
            price_usd_mwh
        )
        SELECT
            %(iso_code)s,
            %(interval_start_utc)s,
            %(interval_end_utc)s,
            %(load_mw)s,
            %(price_usd_mwh)s
        WHERE NOT EXISTS (
            SELECT 1
            FROM energy_timeseries
            WHERE iso_code = %(iso_code)s
              AND interval_start_utc = %(interval_start_utc)s
        )
        RETURNING *;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, record)
            inserted = cur.fetchone()
            conn.commit()

    return inserted


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.route("/")
def home():
    return jsonify({
        "message": "Use /grid/<iso_code>",
        "supported_regions": list(ISO_MAP.keys()),
        "examples": [
            "/grid/caiso",
            "/grid/ercot",
            "/grid/pjm",
            "/grid/nyiso",
            "/grid/isone",
            "/grid/miso",
            "/grid/spp",
        ],
    })


@app.route("/grid/<iso_code>")
def grid(iso_code):
    try:
        iso_code = iso_code.lower()

        if iso_code not in ISO_MAP:
            return jsonify({
                "error": "Unsupported ISO region",
                "supported_regions": list(ISO_MAP.keys()),
            }), 400

        iso = ISO_MAP[iso_code]()
        query_date = date.today()

        load_df = iso.get_load(date=query_date)

        if load_df.empty:
            return jsonify({
                "iso_code": iso_code,
                "error": "No load data returned",
                "query_date": str(query_date),
            }), 404

        load_row = load_df.iloc[-1].to_dict()

        interval_start = pick(load_row, [
            "Interval Start",
            "Time",
            "Interval Beginning",
        ])

        interval_end = pick(load_row, [
            "Interval End",
            "Time",
            "Interval Ending",
        ])

        load_mw = pick(load_row, [
            "Load",
            "Demand",
            "Current demand",
            "System Total",
            "Load MW",
        ])

        interval_start_utc = to_utc(interval_start)
        interval_end_utc = to_utc(interval_end)

        # If the source only gives one timestamp, use it for both start/end.
        if interval_end_utc is None:
            interval_end_utc = interval_start_utc

        record = {
            "iso_code": iso_code.upper(),
            "interval_start_utc": interval_start_utc,
            "interval_end_utc": interval_end_utc,
            "load_mw": load_mw,
            "price_usd_mwh": None,
        }

        inserted = insert_energy_timeseries(record)

        result = {
            "iso_code": record["iso_code"],
            "interval_start_utc": str(record["interval_start_utc"]),
            "interval_end_utc": str(record["interval_end_utc"]),
            "load_mw": float(record["load_mw"]) if record["load_mw"] is not None else None,
            "price_usd_mwh": record["price_usd_mwh"],
            "db_action": "inserted" if inserted else "already_exists",
        }

        print(result)
        return jsonify(result)

    except Exception as e:
        print("ERROR:", repr(e))
        return jsonify({
            "iso_code": iso_code,
            "error": repr(e),
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )