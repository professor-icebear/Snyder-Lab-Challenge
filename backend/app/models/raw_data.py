from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class RawData(Base):
    __tablename__ = "raw_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    is_imputed = Column(Boolean, default=False, index=True)
    imputation_method = Column(String(100))
    imputed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<RawData(id={self.id}, user_id={self.user_id}, metric='{self.metric_name}', timestamp='{self.timestamp}', is_imputed={self.is_imputed})>"
    
    def to_dict(self):
        """Convert raw data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metric_name': self.metric_name,
            'value': self.value,
            'is_imputed': self.is_imputed,
            'imputation_method': self.imputation_method,
            'imputed_at': self.imputed_at.isoformat() if self.imputed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 