# Use an official Python runtime as a parent image
FROM python:3.9-slim-bullseye

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies needed for the application or building wheels
# We only keep curl and gnupg if they are strictly necessary for app dependencies
# lsb-release might be needed by some build scripts, but often not.
# For now, let's assume only basic build tools are needed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    # Add any build-essential type packages if pip install fails for some C extensions
    # For example: gcc libpq-dev (if psycopg2 was not -binary)
    # For now, keeping it minimal
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir is good practice for smaller images
RUN pip install --no-cache-dir -r requirements.txt

# Create target directories explicitly
RUN mkdir -p /app/app && mkdir -p /app/alembic

# Copy application code and necessary configuration files
COPY ./app/ /app/app/
COPY ./alembic/ /app/alembic/
COPY alembic.ini .
COPY firebase.json .
COPY .env .

# Expose port for FastAPI application
EXPOSE 8000

# Command to run the application
# This will be overridden by docker-compose.yml but is good for direct image runs
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
