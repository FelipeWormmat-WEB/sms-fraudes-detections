from sqlalchemy import Column, Integer, String, Float, DateTime, func
from .session import Base
from pydantic import BaseModel

class SMSLog(Base):
    __tablename__ = "sms_logs"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    prediction = Column(String, nullable=False)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ModelMetrics(Base):
    __tablename__ = "model_metrics"
    id = Column(Integer, primary_key=True, index=True)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

class MessageInput(BaseModel):
    message: str
