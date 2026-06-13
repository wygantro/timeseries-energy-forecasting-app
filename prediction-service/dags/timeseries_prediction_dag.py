# dags/timeseries_predictions_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import logging

API_URL = "http://your-timeseries-service:8000/predict"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

def call_timeseries_prediction():
    payload = {
        "model_name": "timeseries_forecast",
        "horizon": 10,
        "frequency": "10min"
    }

    response = requests.post(API_URL, json=payload, timeout=30)

    if response.status_code != 200:
        raise Exception(
            f"Prediction API failed: {response.status_code} - {response.text}"
        )

    result = response.json()
    logging.info("Timeseries prediction result: %s", result)

    return result

with DAG(
    dag_id="timeseries_predictions_every_10_minutes",
    default_args=default_args,
    description="Calls timeseries prediction service every 10 minutes",
    schedule="*/10 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["timeseries", "prediction", "ml"],
) as dag:

    run_prediction = PythonOperator(
        task_id="call_timeseries_prediction_api",
        python_callable=call_timeseries_prediction,
    )