print('participants.py imported')
from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.schemas.participant import ParticipantCreate, ParticipantUpdate, ParticipantOut
from app.models.participant import Participant, Base
from app.models.raw_data import RawData
from app.core.mail import send_email

router = APIRouter(prefix="/participants", tags=["Participants"])

class EmailSchema(BaseModel):
    subject: str
    body: str

# Dependency to get DB session

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

@router.post("/", response_model=ParticipantOut, status_code=status.HTTP_201_CREATED)
def create_participant(participant: ParticipantCreate, db: Session = Depends(get_db_session)):
    db_participant = Participant(**participant.dict())
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant

@router.get("/", response_model=List[ParticipantOut])
def list_participants(db: Session = Depends(get_db_session)):
    return db.query(Participant).all()

@router.get("/{participant_id}", response_model=ParticipantOut)
def get_participant(participant_id: int, db: Session = Depends(get_db_session)):
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant

@router.post("/{participant_id}/contact", status_code=status.HTTP_200_OK)
async def contact_participant(
    participant_id: int,
    email: EmailSchema,
    db: Session = Depends(get_db_session)
):
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    try:
        await send_email(
            subject=email.subject,
            recipients=[participant.email],
            body=email.body
        )
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{participant_id}/metrics")
def get_participant_metrics(
    participant_id: int,
    db: Session = Depends(get_db_session),
    metrics: List[str] = Query(...),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...)
) -> Dict[str, List[Dict]]:
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    results = {}
    for metric in metrics:
        data = db.query(RawData).filter(
            RawData.user_id == participant_id,
            RawData.metric_name == metric,
            RawData.timestamp >= start_date,
            RawData.timestamp <= end_date
        ).order_by(RawData.timestamp).all()
        results[metric] = [{"timestamp": d.timestamp, "value": d.value, "is_imputed": d.is_imputed} for d in data]

    return results

@router.put("/{participant_id}", response_model=ParticipantOut)
def update_participant(participant_id: int, update: ParticipantUpdate, db: Session = Depends(get_db_session)):
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    for key, value in update.dict(exclude_unset=True).items():
        setattr(participant, key, value)
    db.commit()
    db.refresh(participant)
    return participant

@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(participant_id: int, db: Session = Depends(get_db_session)):
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    db.delete(participant)
    db.commit()
    return None 