FROM python:3.9-slim

# Install cron and other dependencies
RUN apt-get update && apt-get install -y \
    cron \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ingest/ ./ingest/
COPY ingest/data/ ./ingest/data/

# Create last_run.txt if it doesn't exist
RUN echo "2024-01-01T00:00:00" > last_run.txt

# Create cron job file
RUN echo "0 1 * * * cd /app && python ingest/ingest.py >> /var/log/cron.log 2>&1" > /etc/cron.d/ingest-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/ingest-cron

# Apply cron job
RUN crontab /etc/cron.d/ingest-cron

# Create log file
RUN touch /var/log/cron.log

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose port (if needed for any web interface)
EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["./entrypoint.sh"]