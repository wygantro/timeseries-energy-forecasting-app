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

#from apscheduler.schedulers.background import BackgroundScheduler
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
db = SQLAlchemy(engine_options=dict(
    pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=2
))
db.init_app(app)

# Initialize Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)

logger = logging.getLogger()

@app.route('/', methods=['GET'])
def hello_world():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f'Hello, World! Current time is {current_time}'

@app.get("/health")
def health():
    return jsonify({"ok": True})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')


