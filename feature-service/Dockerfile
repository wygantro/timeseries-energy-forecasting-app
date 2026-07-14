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