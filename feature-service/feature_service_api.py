# ./feature_service_api.py

from flask import Flask, jsonify
from datetime import datetime#, timezone, timedelta
# import time
from flask_sqlalchemy import SQLAlchemy
# # from app.commit import current_datetime
# # from app.get_data import btc_minute_price, eth_minute_price, btc_hour_price, eth_hour_price, btc_daily_price, eth_daily_price, get_last_closed_daily_candle, get_last_closed_minute_candle, hour_window, ohlcv_vwap_from_minutes
# from sqlalchemy import text
import logging
# import os
# import pandas as pd


import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, jsonify

from app.gridstatus_ingest import db, ingest_all, ingest_iso


app = Flask(__name__)

# Public Connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pzQNLo8m$cULtO3c@34.60.16.16:5432/feature-service-db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# # Initialize Cloud SQL Connection
# app.config["SQLALCHEMY_DATABASE_URI"] = (
#     "postgresql+psycopg2://{user}:{pwd}@/{db}"
#     "?host=/cloudsql/{instance}"
# ).format(
#     user="user",
#     pwd="pzQNLo8m$cULtO3c",
#     db="feature-service-db",
#     instance="timeseries-energy-forecasting:us-central1:timeseries-energy-forecasting-instance"  # project:region:instance
# )

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(engine_options=dict(
#     pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=2
# ))
db.init_app(app)

# Initialize Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)

logger = logging.getLogger()

# @app.route('/', methods=['GET'])
# def hello_world():
#     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     return f'Hello, World! Current time is {current_time}'

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.get("/api/grid/load/<iso_code>")
def get_and_store_iso(iso_code):
    """Fetch and store one ISO."""
    try:
        logger.info("Starting ISO ingest: %s", iso_code.upper())
        result = ingest_iso(iso_code)
        logger.info("Finished ISO ingest: %s", iso_code.upper())

        return jsonify({"ok": True, "data": result})

    except Exception as e:
        db.session.rollback()
        logger.exception("ISO ingest failed: %s", iso_code.upper())

        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/grid/ingest")
def manual_ingest_all():
    """Fetch and store all configured ISOs."""
    logger.info("Starting manual all-ISO ingest")
    results = ingest_all()
    logger.info("Finished manual all-ISO ingest")

    return jsonify(results)


def scheduled_ingest():
    """Run scheduled ingest inside the Flask app context."""
    with app.app_context():
        logger.info("Starting scheduled all-ISO ingest")
        results = ingest_all()
        logger.info("Finished scheduled all-ISO ingest: %s", results)


scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(
    scheduled_ingest,
    trigger="interval",
    minutes=1,
    id="gridstatus_ingest_every_5_min",
    replace_existing=True,
)
scheduler.start()

logger.info("GridStatus scheduler started")


if __name__ == "__main__":
    with app.app_context():
        # Uncomment only if SQLAlchemy should create missing tables.
        # db.create_all()
        pass

    logger.info("Starting Flask API server on port 5050")
    app.run(host="0.0.0.0", port=5050)

# if __name__ == '__main__':
#     app.run(debug=False, host='0.0.0.0')


