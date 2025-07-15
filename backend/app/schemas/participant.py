from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ParticipantBase(BaseModel):
    email: str
    name: Optional[str] = None
    study_start_date: Optional[date] = None
    study_end_date: Optional[date] = None
    fitbit_token: Optional[str] = None
    last_upload_date: Optional[datetime] = None
    adherence_percentage: Optional[float] = 0.0
    sleep_threshold: Optional[int] = 7
    overall_threshold: Optional[int] = 70

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantUpdate(ParticipantBase):
    pass

class ParticipantOut(ParticipantBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 