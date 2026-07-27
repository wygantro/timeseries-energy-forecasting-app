# app.py

import json
import os
from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///predictions.db",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Database model
# ---------------------------------------------------------------------------

class PredictionRecord(db.Model):
    __tablename__ = "prediction_records"

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    prediction_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "model_name": self.model_name,
            "input": json.loads(self.input_data),
            "prediction": json.loads(self.prediction_data),
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Placeholder model layer
# ---------------------------------------------------------------------------

class BaseTimeSeriesModel:
    def predict(
        self,
        observations: list[float],
        horizon: int,
    ) -> list[float]:
        raise NotImplementedError


class NaiveTimeSeriesModel(BaseTimeSeriesModel):
    """
    Placeholder model that repeats the most recent observation.

    Replace this class with an adapter for your actual model, such as:
    - scikit-learn
    - statsmodels
    - Prophet
    - PyTorch
    - TensorFlow
    """

    def predict(
        self,
        observations: list[float],
        horizon: int,
    ) -> list[float]:
        latest_value = observations[-1]
        return [latest_value] * horizon


MODEL_REGISTRY: dict[str, BaseTimeSeriesModel] = {
    "naive": NaiveTimeSeriesModel(),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_json_body() -> dict[str, Any]:
    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        raise ValueError("Request body must be a JSON object.")

    return body


def validate_prediction_request(
    body: dict[str, Any],
) -> tuple[str, list[float], int]:
    model_name = body.get("model_name", "naive")
    observations = body.get("observations")
    horizon = body.get("horizon", 1)

    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model_name: {model_name}")

    if not isinstance(observations, list) or not observations:
        raise ValueError(
            "observations must be a non-empty array of numbers."
        )

    if any(
        not isinstance(value, (int, float)) or isinstance(value, bool)
        for value in observations
    ):
        raise ValueError("Every observation must be numeric.")

    if not isinstance(horizon, int) or isinstance(horizon, bool):
        raise ValueError("horizon must be an integer.")

    if horizon < 1 or horizon > 1000:
        raise ValueError("horizon must be between 1 and 1000.")

    normalized_observations = [
        float(value) for value in observations
    ]

    return model_name, normalized_observations, horizon


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/models")
def list_models():
    return jsonify({
        "models": list(MODEL_REGISTRY.keys()),
    })


@app.post("/predict")
def predict():
    try:
        body = get_json_body()

        model_name, observations, horizon = (
            validate_prediction_request(body)
        )

        model = MODEL_REGISTRY[model_name]
        predictions = model.predict(
            observations=observations,
            horizon=horizon,
        )

        record = PredictionRecord(
            model_name=model_name,
            input_data=json.dumps({
                "observations": observations,
                "horizon": horizon,
            }),
            prediction_data=json.dumps(predictions),
        )

        db.session.add(record)
        db.session.commit()

        return jsonify({
            "prediction_id": record.id,
            "model_name": model_name,
            "horizon": horizon,
            "predictions": predictions,
            "created_at": record.created_at.isoformat(),
        }), 201

    except ValueError as error:
        return jsonify({
            "error": "invalid_request",
            "message": str(error),
        }), 400

    except Exception:
        db.session.rollback()
        app.logger.exception("Prediction request failed.")

        return jsonify({
            "error": "internal_server_error",
            "message": "The prediction request could not be completed.",
        }), 500


@app.get("/predictions")
def list_predictions():
    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(limit, 100))

    records = (
        PredictionRecord.query
        .order_by(PredictionRecord.created_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify({
        "predictions": [record.to_dict() for record in records],
    })


@app.get("/predictions/<int:prediction_id>")
def get_prediction(prediction_id: int):
    record = db.session.get(PredictionRecord, prediction_id)

    if record is None:
        return jsonify({
            "error": "not_found",
            "message": "Prediction record not found.",
        }), 404

    return jsonify(record.to_dict())


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )