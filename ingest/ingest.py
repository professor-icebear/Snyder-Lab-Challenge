import csv
import json
import psycopg2
import os
from datetime import datetime, timedelta
import ast
import re
import threading
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import uvicorn

# Increase CSV field size limit for large files
csv.field_size_limit(2147483647)

# Prometheus metrics
ingestion_error_count = Counter(
    'ingestion_error_count', 'Number of ingestion errors encountered by the ingestion script')
ingestion_latency_seconds = Histogram(
    'ingestion_latency_seconds', 'Latency of ingestion process in seconds')
ingestion_rows_total = Gauge(
    'ingestion_rows_total', 'Total number of rows ingested in the last run')

def convert_np_float64(value_str):
    """Convert np.float64 string to float"""
    if isinstance(value_str, str) and 'np.float64(' in value_str:
        # Extract the number from np.float64(number)
        match = re.search(r'np\.float64\(([^)]+)\)', value_str)
        if match:
            return float(match.group(1))
    return value_str

def safe_eval_list(value_str):
    """Safely evaluate stringified list of dictionaries"""
    try:
        # Handle the case where the string might be a list of dictionaries
        if value_str.startswith('[') and value_str.endswith(']'):
            # Replace np.float64() calls with just the number
            cleaned_str = re.sub(r'np\.float64\(([^)]+)\)', r'\1', value_str)
            # Use ast.literal_eval for safer evaluation
            return ast.literal_eval(cleaned_str)
        return []
    except (ValueError, SyntaxError):
        return []

def process_activity():
    """Process activity.csv file"""
    rows = []
    try:
        with open('ingest/data/activity.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                timestamp = datetime.fromisoformat(row['dateTime'].replace('Z', '+00:00'))
                value = float(row['value'])
                rows.append({
                    'user_id': 1,
                    'timestamp': timestamp,
                    'metric_name': 'activity',
                    'value': value
                })
    except Exception as e:
        print(f"Error processing activity.csv: {e}")
    return rows

def process_breathing_rate():
    """Process breathing_rate.csv file"""
    rows = []
    try:
        with open('ingest/data/breathing_rate.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse the stringified list of dictionaries
                    br_data = safe_eval_list(row['br'])
                    if not br_data:
                        continue
                    
                    # Extract timestamp from the first item
                    timestamp_str = br_data[0].get('dateTime', '')
                    if not timestamp_str:
                        continue
                    
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Extract breathing rate values from different sleep stages
                    for item in br_data:
                        if 'value' in item and isinstance(item['value'], dict):
                            for stage, rate_data in item['value'].items():
                                if isinstance(rate_data, dict) and 'breathingRate' in rate_data:
                                    rate = convert_np_float64(rate_data['breathingRate'])
                                    if isinstance(rate, (int, float)):
                                        rows.append({
                                            'user_id': 1,
                                            'timestamp': timestamp,
                                            'metric_name': f'breathing_rate_{stage}',
                                            'value': float(rate)
                                        })
                                elif isinstance(rate_data, (int, float)):
                                    # Handle case where breathingRate is directly a number
                                    rate = convert_np_float64(rate_data)
                                    if isinstance(rate, (int, float)):
                                        rows.append({
                                            'user_id': 1,
                                            'timestamp': timestamp,
                                            'metric_name': f'breathing_rate_{stage}',
                                            'value': float(rate)
                                        })
                except Exception as e:
                    print(f"Error processing breathing rate row: {e}")
                    continue
    except Exception as e:
        print(f"Error processing breathing_rate.csv: {e}")
    return rows

def process_spo2():
    """Process spo2.csv file"""
    rows = []
    try:
        with open('ingest/data/spo2.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse the stringified list of dictionaries
                    minutes_data = safe_eval_list(row['minutes'])
                    if not minutes_data:
                        continue
                    
                    # Extract timestamp from dateTime column
                    timestamp_str = row.get('dateTime', '')
                    if not timestamp_str:
                        continue
                    
                    base_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Process each minute's data
                    for item in minutes_data:
                        if 'value' in item and 'minute' in item:
                            value = convert_np_float64(item['value'])
                            if isinstance(value, (int, float)):
                                # Create timestamp for this minute
                                minute_str = item['minute']
                                try:
                                    # Parse the full timestamp from minute field
                                    timestamp = datetime.fromisoformat(minute_str.replace('Z', '+00:00'))
                                    
                                    rows.append({
                                        'user_id': 1,
                                        'timestamp': timestamp,
                                        'metric_name': 'spo2',
                                        'value': float(value)
                                    })
                                except (ValueError, AttributeError):
                                    continue
                except Exception as e:
                    print(f"Error processing SPO2 row: {e}")
                    continue
    except Exception as e:
        print(f"Error processing spo2.csv: {e}")
    return rows

def process_heart_rate():
    """Process heart_rate.csv file"""
    rows = []
    try:
        with open('ingest/data/heart_rate.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse the stringified list of dictionaries
                    activities_data = safe_eval_list(row.get('activities-heart-intraday', '[]'))
                    if not activities_data:
                        continue
                    
                    # Extract timestamp from dateTime column
                    timestamp_str = row.get('dateTime', '')
                    if not timestamp_str:
                        continue
                    
                    base_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Process each activity's data
                    for activity in activities_data:
                        if 'dataset' in activity and isinstance(activity['dataset'], list):
                            for data_point in activity['dataset']:
                                if 'time' in data_point and 'value' in data_point:
                                    value = convert_np_float64(data_point['value'])
                                    if isinstance(value, (int, float)):
                                        # Create timestamp for this data point
                                        time_str = data_point['time']
                                        try:
                                            hour, minute, second = map(int, time_str.split(':'))
                                            timestamp = base_timestamp.replace(hour=hour, minute=minute, second=second, microsecond=0)
                                            
                                            rows.append({
                                                'user_id': 1,
                                                'timestamp': timestamp,
                                                'metric_name': 'heart_rate',
                                                'value': float(value)
                                            })
                                        except (ValueError, AttributeError):
                                            continue
                except Exception as e:
                    print(f"Error processing heart rate row: {e}")
                    continue
    except Exception as e:
        print(f"Error processing heart_rate.csv: {e}")
    return rows

def process_hrv():
    """Process hrv.csv file"""
    rows = []
    try:
        with open('ingest/data/hrv.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse the stringified list of dictionaries
                    hrv_data = safe_eval_list(row.get('hrv', '[]'))
                    if not hrv_data:
                        continue
                    
                    # Extract timestamp from dateTime column
                    timestamp_str = row.get('dateTime', '')
                    if not timestamp_str:
                        continue
                    
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Process HRV data
                    for item in hrv_data:
                        if 'value' in item:
                            value = convert_np_float64(item['value'])
                            if isinstance(value, (int, float)):
                                rows.append({
                                    'user_id': 1,
                                    'timestamp': timestamp,
                                    'metric_name': 'hrv',
                                    'value': float(value)
                                })
                except Exception as e:
                    print(f"Error processing HRV row: {e}")
                    continue
    except Exception as e:
        print(f"Error processing hrv.csv: {e}")
    return rows

def process_active_zone_minutes():
    """Process active_zone_minutes.csv file"""
    rows = []
    try:
        with open('ingest/data/active_zone_minutes.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse the stringified list of dictionaries
                    activities_data = safe_eval_list(row.get('activities-active-zone-minutes', '[]'))
                    if not activities_data:
                        continue
                    
                    # Extract timestamp from dateTime column
                    timestamp_str = row.get('dateTime', '')
                    if not timestamp_str:
                        continue
                    
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Process active zone minutes data
                    for activity in activities_data:
                        if 'value' in activity and isinstance(activity['value'], dict):
                            for zone, minutes in activity['value'].items():
                                if isinstance(minutes, (int, float)):
                                    rows.append({
                                        'user_id': 1,
                                        'timestamp': timestamp,
                                        'metric_name': f'active_zone_minutes_{zone}',
                                        'value': float(minutes)
                                    })
                except Exception as e:
                    print(f"Error processing active zone minutes row: {e}")
                    continue
    except Exception as e:
        print(f"Error processing active_zone_minutes.csv: {e}")
    return rows

def process_generic_csv(filename, metric_name):
    """Process generic CSV files with dateTime and value columns"""
    rows = []
    try:
        with open(f'ingest/data/{filename}', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    timestamp = datetime.fromisoformat(row['dateTime'].replace('Z', '+00:00'))
                    value = float(row['value'])
                    rows.append({
                        'user_id': 1,
                        'timestamp': timestamp,
                        'metric_name': metric_name,
                        'value': value
                    })
                except Exception as e:
                    print(f"Error processing {filename} row: {e}")
                    continue
    except Exception as e:
        print(f"Error processing {filename}: {e}")
    return rows

def start_metrics_server():
    # Start Prometheus metrics server on port 8000
    start_http_server(8000)

ingestion_app = FastAPI()

@ingestion_app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@ingestion_app.post("/run_ingestion")
def run_ingestion():
    result = run_ingestion_job()
    return {"result": result}

def run_ingestion_job():
    start_time = time.time()
    error_occurred = False
    all_rows = []
    try:
        # Process each file type
        all_rows.extend(process_activity())
        all_rows.extend(process_breathing_rate())
        all_rows.extend(process_spo2())
        all_rows.extend(process_heart_rate())
        all_rows.extend(process_hrv())
        all_rows.extend(process_active_zone_minutes())

        # Connect to database and insert data
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'timescaledb'),
            port=os.environ.get('DB_PORT', '5432'),
            database=os.environ.get('DB_NAME', 'fitbit_data'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASS', 'password')
        )
        cursor = conn.cursor()

        # Create raw_data table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_data (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                metric_name TEXT NOT NULL,
                value DOUBLE PRECISION,
                is_imputed BOOLEAN DEFAULT FALSE,
                UNIQUE(user_id, timestamp, metric_name)
            );
        """)

        # Create TimescaleDB hypertable if not already created
        try:
            cursor.execute("SELECT create_hypertable('raw_data', 'timestamp');")
        except psycopg2.Error as e:
            if e.pgcode == '42710': # duplicate_table, for hypertable
                conn.rollback()
                cursor = conn.cursor()
                print("Hypertable 'raw_data' already exists.")
            else:
                raise

        # Insert data
        for row in all_rows:
            cursor.execute("""
                INSERT INTO raw_data (user_id, timestamp, metric_name, value)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, timestamp, metric_name) DO NOTHING
            """, (row['user_id'], row['timestamp'], row['metric_name'], row['value']))

        conn.commit()
        cursor.close()
        conn.close()

        total_rows = len(all_rows)
        ingestion_rows_total.set(total_rows)
        print(f"Found {total_rows} new data points")
        print("Data ingestion completed")
        return f"Ingested {total_rows} rows"

    except Exception as e:
        ingestion_error_count.inc()
        error_occurred = True
        print(f"Database error: {e}")
        return f"Database error: {e}"
    finally:
        elapsed = time.time() - start_time
        ingestion_latency_seconds.observe(elapsed)

if __name__ == "__main__":
    # Start FastAPI server for metrics and ingestion trigger
    uvicorn.run("ingest.ingest:ingestion_app", host="0.0.0.0", port=8000, reload=False)
