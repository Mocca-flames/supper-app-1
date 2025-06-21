#!/bin/bash
set -e

# Default values, can be overridden by environment variables
# In docker-compose, PG_HOST should be 'db' and REDIS_HOST should be 'redis'
PG_HOST="${PG_HOST:-db}"
PG_PORT="${PG_PORT:-5432}"
PG_USER="${POSTGRES_USER:-postgres}" # POSTGRES_USER will be from .env via docker-compose
PG_DB_NAME="${POSTGRES_DB:-postgres}" # POSTGRES_DB will be from .env via docker-compose

REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo "Waiting for PostgreSQL to be ready at ${PG_HOST}:${PG_PORT} with user ${PG_USER} on db ${PG_DB_NAME}..."
# pg_isready might not be sufficient if the DB itself isn't fully ready or user cannot connect.
# A more robust check would be to try to connect.
# However, pg_isready is a good first step and often available.
# The -q flag makes it quiet. It exits with 0 if ready, 1 if rejected, 2 if no response, 3 if no attempt made (bad params).
until pg_isready -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DB_NAME}" -q; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
>&2 echo "PostgreSQL is up - continuing"

echo "Waiting for Redis to be ready at ${REDIS_HOST}:${REDIS_PORT}..."
until redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping | grep -q PONG; do
  >&2 echo "Redis is unavailable - sleeping"
  sleep 1
done
>&2 echo "Redis is up - continuing"

echo "All services are ready. Starting application..."
# Execute the original command for FastAPI
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
