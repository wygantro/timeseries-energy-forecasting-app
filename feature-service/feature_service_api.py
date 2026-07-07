# ./feature_service_api.py


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

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(engine_options=dict(
#     pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=2
# ))
# db.init_app(app)

## Initialize Logging Configuration
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
# )

# logger = logging.getLogger()


from flask import Flask, jsonify
from datetime import date, timedelta

from gridstatus import CAISO, Ercot, PJM, NYISO, ISONE, MISO, SPP

app = Flask(__name__)

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
        if name in row:
            return row[name]
    return None

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
        query_date = date.today() - timedelta(days=1)

        load_df = iso.get_load(date=query_date)

        if load_df.empty:
            return jsonify({
                "iso_code": iso_code,
                "error": "No load data returned",
                "query_date": str(query_date),
            }), 404

        load_row = load_df.iloc[-1].to_dict()

        result = {
            "iso_code": iso_code,
            "time_stamp": str(
                pick(load_row, ["Time", "Interval Start", "Interval End"])
            ),
            "electric_demand": pick(
                load_row,
                [
                    "Load",
                    "Demand",
                    "Current demand",
                    "System Total",
                    "Load MW",
                ],
            ),
            "location_id": iso_code.upper(),
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
    app.run(debug=True, port=5000)