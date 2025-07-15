#!/bin/bash

# Start cron service
service cron start

# Wait for database to be ready (optional)
echo "Waiting for database to be ready..."
sleep 10

# Start FastAPI server for metrics and ingestion trigger in the background
uvicorn ingest.ingest:ingestion_app --host 0.0.0.0 --port 8000 &

# Keep container running
echo "Cron service started. FastAPI server running on port 8000. Container will run indefinitely."
echo "Cron logs will be written to /var/log/cron.log"
echo "To view logs: docker exec <container_name> tail -f /var/log/cron.log"

tail -f /var/log/cron.log 