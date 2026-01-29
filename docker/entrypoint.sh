#!/bin/bash
set -e

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready"

# Wait for MongoDB
echo "Waiting for MongoDB..."
while ! nc -z mongo 27017; do
  sleep 1
done
echo "MongoDB is ready"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start application
echo "Starting FastAPI application..."
exec uvicorn app.api:app --host 0.0.0.0 --port 8000
