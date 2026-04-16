FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Data directory for SQLite (mount as volume in docker-compose)
RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/data/compliance.db

WORKDIR /app/src
CMD ["python", "monitor.py"]
