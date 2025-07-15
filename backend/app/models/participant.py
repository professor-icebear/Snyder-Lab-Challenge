from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Text
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    study_start_date = Column(Date)
    study_end_date = Column(Date)
    fitbit_token = Column(Text)
    last_upload_date = Column(DateTime(timezone=True))
    adherence_percentage = Column(Numeric(5, 2), default=0.0)
    sleep_threshold = Column(Integer, default=7)
    overall_threshold = Column(Integer, default=70)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships - commented out for now to avoid circular imports
    # communication_logs = relationship("CommunicationLog", back_populates="participant", cascade="all, delete-orphan")
    # adherence_history = relationship("AdherenceHistory", back_populates="participant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Participant(id={self.id}, email='{self.email}', name='{self.name}')>"
    
    def to_dict(self):
        """Convert participant to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'study_start_date': self.study_start_date.isoformat() if self.study_start_date else None,
            'study_end_date': self.study_end_date.isoformat() if self.study_end_date else None,
            'fitbit_token': self.fitbit_token,
            'last_upload_date': self.last_upload_date.isoformat() if self.last_upload_date else None,
            'adherence_percentage': float(self.adherence_percentage) if self.adherence_percentage else 0.0,
            'sleep_threshold': self.sleep_threshold,
            'overall_threshold': self.overall_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 