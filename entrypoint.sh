#!/bin/sh
set -e

# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start Uvicorn server
echo "Starting Uvicorn server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
