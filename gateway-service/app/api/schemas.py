from datetime import datetime
from pydantic import BaseModel

class SMSRequest(BaseModel):
    message: str

class SMSResponse(BaseModel):
    message: str
    prediction: str
    confidence: float
    status: str

class SMSLogResponse(BaseModel):
    message: str
    prediction: str
    confidence: float
    created_at: datetime