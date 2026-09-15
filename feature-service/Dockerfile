# Dockerfile

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY config/requirements.txt ./config/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ./config/requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "feature_service_api.py"]

DB_NAME = os.getenv("DB_NAME", "feature-service-db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "%,f_KA}i@e1KX0`(")