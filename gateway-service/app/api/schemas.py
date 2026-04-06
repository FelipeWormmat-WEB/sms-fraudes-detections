from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class SMSRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4096)
    ground_truth: Optional[str] = Field(default=None, description="Optional true label: spam or ham")

class SMSResponse(BaseModel):
    message: str
    prediction: str
    confidence: float
    source: str
    status: str

class SMSLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    prediction: str
    confidence: float
    source: str
    ground_truth: Optional[str] = None
    created_at: datetime


class CreateClientRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    plan: str = Field(default="starter", min_length=2, max_length=40)
    monthly_quota: int = Field(default=50000, ge=1, le=1_000_000)


class CreateClientResponse(BaseModel):
    client_id: int
    name: str
    plan: str
    monthly_quota: int
    api_key: str
    created_at: datetime


class UsageSummaryResponse(BaseModel):
    client_id: int
    month: str
    used: int
    quota: int
    remaining: int
