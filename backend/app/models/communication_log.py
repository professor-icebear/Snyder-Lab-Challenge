from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class CommunicationLog(Base):
    __tablename__ = "communication_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True)
    email_type = Column(String(50), nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    message_content = Column(Text)
    threshold_triggered = Column(String(100))
    email_status = Column(String(20), default="sent")
    recipient_email = Column(String(255))
    
    # Relationship - commented out for now to avoid circular imports
    # participant = relationship("Participant", back_populates="communication_logs")
    
    def __repr__(self):
        return f"<CommunicationLog(id={self.id}, participant_id={self.participant_id}, email_type='{self.email_type}', sent_at='{self.sent_at}')>"
    
    def to_dict(self):
        """Convert communication log to dictionary"""
        return {
            'id': self.id,
            'participant_id': self.participant_id,
            'email_type': self.email_type,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'message_content': self.message_content,
            'threshold_triggered': self.threshold_triggered,
            'email_status': self.email_status,
            'recipient_email': self.recipient_email
        } 