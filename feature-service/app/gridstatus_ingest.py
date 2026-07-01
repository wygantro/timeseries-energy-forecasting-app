# app/gridstatus_ingest.py

from datetime import timedelta
from decimal import Decimal

import gridstatus
import pandas as pd
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Supported GridStatus ISOs.
ISOS = {
    "ERCOT": gridstatus.Ercot(),
    "PJM": gridstatus.PJM(),
    "NYISO": gridstatus.NYISO(),
    "ISONE": gridstatus.ISONE(),
    "SPP": gridstatus.SPP(),
}


class GridLoadPrice(db.Model):
    """SQLAlchemy model for grid_load_prices."""

    __tablename__ = "grid_load_prices"

    iso_code = db.Column(
        db.String(20),
        db.ForeignKey("energy_locations.iso_code"),
        primary_key=True,
        nullable=False,
    )

    interval_start_utc = db.Column(
        db.DateTime(timezone=True),
        primary_key=True,
        nullable=False,
    )

    interval_end_utc = db.Column(
        db.DateTime(timezone=True),
        primary_key=True,
        nullable=False,
    )

    load_mw = db.Column(db.Numeric(14, 4))
    price_usd_mwh = db.Column(db.Numeric(14, 4))

    ingested_at_utc = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )


def utc_ts(value):
    """Convert a timestamp to timezone-aware UTC."""
    ts = pd.Timestamp(value)

    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")

    return ts.tz_convert("UTC").to_pydatetime()


def pick_col(df, names):
    """Return the first matching column from a list of candidates."""
    normalized = {
        col.lower().replace(" ", "_"): col
        for col in df.columns
    }

    for name in names:
        key = name.lower().replace(" ", "_")
        if key in normalized:
            return normalized[key]

    return None


def latest_load_row(iso_code):
    """Fetch and normalize the latest ISO system load."""
    iso_code = iso_code.upper()

    if iso_code not in ISOS:
        raise ValueError(f"Unsupported ISO: {iso_code}")

    df = ISOS[iso_code].get_load("latest")

    if df is None or df.empty:
        raise ValueError(f"No load data returned for {iso_code}")

    # GridStatus column names vary by ISO.
    time_col = pick_col(df, ["interval_start", "time", "timestamp", "datetime"])
    load_col = pick_col(df, ["load", "load_mw", "system_load", "demand"])

    if not time_col or not load_col:
        raise ValueError(f"Unexpected columns for {iso_code}: {list(df.columns)}")

    row = df.sort_values(time_col).tail(1).iloc[0]

    interval_start = utc_ts(row[time_col])
    interval_end = interval_start + timedelta(minutes=5)

    return {
        "iso_code": iso_code,
        "interval_start_utc": interval_start,
        "interval_end_utc": interval_end,
        "load_mw": Decimal(str(row[load_col])),
        "price_usd_mwh": None,
    }


def upsert_grid_row(row):
    """Insert or update one grid_load_prices record."""
    existing = GridLoadPrice.query.get(
        (
            row["iso_code"],
            row["interval_start_utc"],
            row["interval_end_utc"],
        )
    )

    if existing:
        existing.load_mw = row["load_mw"]

        if row.get("price_usd_mwh") is not None:
            existing.price_usd_mwh = row["price_usd_mwh"]
    else:
        db.session.add(GridLoadPrice(**row))

    db.session.commit()


def ingest_iso(iso_code):
    """Download, store, and return the latest data for one ISO."""
    row = latest_load_row(iso_code)
    upsert_grid_row(row)

    return {
        "iso_code": row["iso_code"],
        "interval_start_utc": row["interval_start_utc"].isoformat(),
        "interval_end_utc": row["interval_end_utc"].isoformat(),
        "load_mw": str(row["load_mw"]),
        "price_usd_mwh": row["price_usd_mwh"],
    }


def ingest_all():
    """Download and store latest data for every configured ISO."""
    results = {}

    for iso_code in ISOS:
        try:
            results[iso_code] = {
                "ok": True,
                "data": ingest_iso(iso_code),
            }
        except Exception as e:
            db.session.rollback()
            results[iso_code] = {
                "ok": False,
                "error": str(e),
            }

    return results