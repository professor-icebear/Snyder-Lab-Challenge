from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List
from app.services import adherence
from app.models.participant import Participant
from app.schemas.participant import ParticipantOut

router = APIRouter(prefix="/adherence", tags=["Adherence"])

def get_db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    DATABASE_URL = f"postgresql://{os.environ.get('DB_USER', 'postgres')}:{os.environ.get('DB_PASS', 'password')}@{os.environ.get('DB_HOST', 'timescaledb')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME', 'fitbit_data')}"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/overview")
def adherence_overview(
    db: Session = Depends(get_db_session),
    days: int = Query(30, description="Number of days to look back for adherence calculation")
):
    today = date.today()
    start_date = today - timedelta(days=days-1)
    end_date = today
    participants = db.query(Participant).all()
    overview = []
    for p in participants:
        wear = adherence.calculate_wear_time(db, p.id, start_date, end_date)
        sleep = adherence.calculate_sleep_compliance(db, p.id, start_date, end_date, threshold=p.sleep_threshold or 7)
        recent = adherence.has_recent_upload(db, p.id)
        overall = adherence.calculate_overall_adherence(db, p.id, start_date, end_date, wear_threshold=p.overall_threshold or 70, sleep_threshold=p.sleep_threshold or 7)
        overview.append({
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "wear_time": wear,
            "sleep_compliance": sleep,
            "recent_upload": recent,
            "overall_adherence": overall,
            "has_token": p.fitbit_token is not None
        })
    return overview

@router.get("/{participant_id}")
def participant_adherence(
    participant_id: int,
    db: Session = Depends(get_db_session),
    days: int = Query(30, description="Number of days to look back for adherence calculation")
):
    today = date.today()
    start_date = today - timedelta(days=days-1)
    end_date = today
    p = db.query(Participant).filter(Participant.id == participant_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Participant not found")
    wear = adherence.calculate_wear_time(db, p.id, start_date, end_date)
    sleep = adherence.calculate_sleep_compliance(db, p.id, start_date, end_date, threshold=p.sleep_threshold or 7)
    recent = adherence.has_recent_upload(db, p.id)
    overall = adherence.calculate_overall_adherence(db, p.id, start_date, end_date, wear_threshold=p.overall_threshold or 70, sleep_threshold=p.sleep_threshold or 7)
    return {
        "id": p.id,
        "name": p.name,
        "email": p.email,
        "wear_time": wear,
        "sleep_compliance": sleep,
        "recent_upload": recent,
        "overall_adherence": overall,
        "has_token": p.fitbit_token is not None
    } 