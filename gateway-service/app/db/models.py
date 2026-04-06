from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from .session import Base
from pydantic import BaseModel


class APIClient(Base):
    __tablename__ = "api_clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    plan = Column(String, nullable=False, default="starter")
    api_key_hash = Column(String, unique=True, index=True, nullable=False)
    monthly_quota = Column(Integer, nullable=False, default=50000)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    logs = relationship("SMSLog", back_populates="client")
    usage_events = relationship("APIUsageEvent", back_populates="client")


class APIUsageEvent(Base):
    __tablename__ = "api_usage_events"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("api_clients.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    status = Column(String, nullable=False, default="success")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    client = relationship("APIClient", back_populates="usage_events")


class SMSLog(Base):
    __tablename__ = "sms_logs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("api_clients.id", ondelete="SET NULL"), nullable=True, index=True)
    message = Column(String, nullable=False)
    prediction = Column(String, nullable=False)
    confidence = Column(Float, default=0.0)
    source = Column(String, nullable=False, default="unknown")
    ground_truth = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("APIClient", back_populates="logs")

class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

class MessageInput(BaseModel):
    message: str
    ground_truth: str | None = None
