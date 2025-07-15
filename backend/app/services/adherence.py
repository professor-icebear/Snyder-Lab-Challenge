from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from app.models.raw_data import RawData
from app.models.participant import Participant
from app.models.adherence_history import AdherenceHistory

# --- Wear time calculation ---
def calculate_wear_time(db: Session, user_id: int, start_date: date, end_date: date) -> float:
    """
    Calculate the percentage of time with heart rate data (proxy for device worn).
    Returns percentage (0-100).
    """
    # Get all heart rate data points for the user in the range
    total_minutes = 0
    worn_minutes = 0
    current = start_date
    while current <= end_date:
        # Assume 24*60 minutes per day
        total_minutes += 1440
        # Count heart_rate data points for this day
        count = db.query(RawData).filter(
            RawData.user_id == user_id,
            RawData.metric_name == 'heart_rate',
            RawData.timestamp >= datetime.combine(current, datetime.min.time()),
            RawData.timestamp < datetime.combine(current + timedelta(days=1), datetime.min.time())
        ).count()
        worn_minutes += count
        current += timedelta(days=1)
    if total_minutes == 0:
        return 0.0
    return round(100.0 * worn_minutes / total_minutes, 2)

# --- Sleep compliance calculation ---
def calculate_sleep_compliance(db: Session, user_id: int, start_date: date, end_date: date, threshold: int = 7) -> float:
    """
    Calculate the percentage of days with sleep data present.
    Returns percentage (0-100).
    """
    total_days = (end_date - start_date).days + 1
    days_with_sleep = 0
    current = start_date
    while current <= end_date:
        count = db.query(RawData).filter(
            RawData.user_id == user_id,
            RawData.metric_name.like('sleep%'),
            RawData.timestamp >= datetime.combine(current, datetime.min.time()),
            RawData.timestamp < datetime.combine(current + timedelta(days=1), datetime.min.time())
        ).count()
        if count >= threshold:
            days_with_sleep += 1
        current += timedelta(days=1)
    if total_days == 0:
        return 0.0
    return round(100.0 * days_with_sleep / total_days, 2)

# --- Recent upload check ---
def has_recent_upload(db: Session, user_id: int, hours: int = 48) -> bool:
    """
    Check if the user has uploaded any data in the last N hours.
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    count = db.query(RawData).filter(
        RawData.user_id == user_id,
        RawData.timestamp >= since
    ).count()
    return count > 0

# --- Overall adherence calculation ---
def calculate_overall_adherence(db: Session, user_id: int, start_date: date, end_date: date, wear_threshold: float = 70.0, sleep_threshold: int = 7) -> float:
    """
    Calculate overall adherence as % of days meeting both wear and sleep thresholds.
    """
    total_days = (end_date - start_date).days + 1
    adherent_days = 0
    current = start_date
    while current <= end_date:
        # Wear time for this day
        wear_count = db.query(RawData).filter(
            RawData.user_id == user_id,
            RawData.metric_name == 'heart_rate',
            RawData.timestamp >= datetime.combine(current, datetime.min.time()),
            RawData.timestamp < datetime.combine(current + timedelta(days=1), datetime.min.time())
        ).count()
        # Sleep data for this day
        sleep_count = db.query(RawData).filter(
            RawData.user_id == user_id,
            RawData.metric_name.like('sleep%'),
            RawData.timestamp >= datetime.combine(current, datetime.min.time()),
            RawData.timestamp < datetime.combine(current + timedelta(days=1), datetime.min.time())
        ).count()
        if wear_count >= (1440 * wear_threshold / 100.0) and sleep_count >= sleep_threshold:
            adherent_days += 1
        current += timedelta(days=1)
    if total_days == 0:
        return 0.0
    return round(100.0 * adherent_days / total_days, 2) 