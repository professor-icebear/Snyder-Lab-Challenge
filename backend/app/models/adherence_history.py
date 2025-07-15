from sqlalchemy import Column, Integer, Date, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class AdherenceHistory(Base):
    __tablename__ = "adherence_history"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    wear_time_hours = Column(Numeric(4, 2))
    sleep_data_available = Column(Boolean, default=False)
    data_uploaded = Column(Boolean, default=False)
    adherence_percentage = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship - commented out for now to avoid circular imports
    # participant = relationship("Participant", back_populates="adherence_history")
    
    def __repr__(self):
        return f"<AdherenceHistory(id={self.id}, participant_id={self.participant_id}, date='{self.date}', adherence_percentage={self.adherence_percentage})>"
    
    def to_dict(self):
        """Convert adherence history to dictionary"""
        return {
            'id': self.id,
            'participant_id': self.participant_id,
            'date': self.date.isoformat() if self.date else None,
            'wear_time_hours': float(self.wear_time_hours) if self.wear_time_hours else None,
            'sleep_data_available': self.sleep_data_available,
            'data_uploaded': self.data_uploaded,
            'adherence_percentage': float(self.adherence_percentage) if self.adherence_percentage else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 