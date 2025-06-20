"""
Database Models for Automotive Service Call Transcripts
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class CallSession(BaseModel):
    """Service call session model - represents each unique customer service call"""
    call_id: str = Field(default_factory=lambda: f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    customer_name: str  # Changed from patient_name to customer_name
    customer_phone: str  # Changed from patient_phone to customer_phone
    started_at: datetime = Field(default_factory=datetime.utcnow)

    # Additional automotive-specific fields (optional, stored in database)
    car_model: Optional[str] = None
    service_type: Optional[str] = None  # first_service, second_service

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TranscriptEntry(BaseModel):
    """Individual transcript entry for service conversations"""
    entry_id: str = Field(default_factory=lambda: f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    call_id: str
    speaker: str  # "user" (customer) or "ai" (service assistant)
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Conversion helpers for MongoDB compatibility
def call_session_to_dict(session: CallSession) -> Dict[str, Any]:
    """Convert CallSession to dictionary for MongoDB storage"""
    return {
        "call_id": session.call_id,
        "customer_name": session.customer_name,  # Updated field name
        "customer_phone": session.customer_phone,  # Updated field name
        "started_at": session.started_at,
        "car_model": getattr(session, 'car_model', None),
        "service_type": getattr(session, 'service_type', None)
    }


def transcript_entry_to_dict(entry: TranscriptEntry) -> Dict[str, Any]:
    """Convert TranscriptEntry to dictionary for MongoDB storage"""
    return {
        "entry_id": entry.entry_id,
        "call_id": entry.call_id,
        "speaker": entry.speaker,
        "message": entry.message,
        "timestamp": entry.timestamp
    }


def dict_to_call_session(data: Dict[str, Any]) -> CallSession:
    """Convert dictionary from MongoDB to CallSession"""
    # Handle both old format (patient_*) and new format (customer_*) for backwards compatibility
    customer_name = data.get("customer_name") or data.get("patient_name", "Unknown Customer")
    customer_phone = data.get("customer_phone") or data.get("patient_phone", "Unknown")

    session = CallSession(
        call_id=data["call_id"],
        customer_name=customer_name,
        customer_phone=customer_phone,
        started_at=data["started_at"]
    )

    # Add automotive-specific fields if present
    if "car_model" in data and data["car_model"]:
        session.car_model = data["car_model"]
    if "service_type" in data and data["service_type"]:
        session.service_type = data["service_type"]

    return session


def dict_to_transcript_entry(data: Dict[str, Any]) -> TranscriptEntry:
    """Convert dictionary from MongoDB to TranscriptEntry"""
    return TranscriptEntry(
        entry_id=data["entry_id"],
        call_id=data["call_id"],
        speaker=data["speaker"],
        message=data["message"],
        timestamp=data["timestamp"]
    )
