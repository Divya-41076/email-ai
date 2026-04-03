from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy.dialects.postgresql import JSONB

from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

from app.db.database import Base

# sqlalchemy models - database tables

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, default="default_user")
    gmail_message_id = Column(String, unique=True, index=True)
    subject = Column(String)
    sender = Column(String)
    body = Column(Text)
    received_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("EmailAnalysis", back_populates="email", uselist=False)


class EmailAnalysis(Base):
    __tablename__ = "email_analysis"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    category = Column(String)
    priority = Column(String)
    summary = Column(Text)
    action_items = Column(JSONB)
    automation_action = Column(String)
    status = Column(String, default="queued")
    processed_at = Column(DateTime, default=datetime.utcnow)

    email = relationship("Email", back_populates="analysis")


# ─── Pydantic Models (API Input/Output) ─────────────────────────────

class EmailInput(BaseModel):
    subject: str
    sender: str
    body: str
    user_id: Optional[str] = "default_user"


class AnalysisOutput(BaseModel):
    category: str
    priority: str
    summary: str
    action_items: List[str]
    automation_action: str
    status: str

    class Config:
        from_attributes = True # allows pydantic to read from sqlalchemy model attributes directly


class EmailResponse(BaseModel):
    id: int
    subject: str
    sender: str
    received_at: datetime
    analysis: Optional[AnalysisOutput] = None

    class Config:
        from_attributes = True # allows pydantic to read from sqlalchemy model attributes directly


# backend returns sqlalchemy objects like
# email = db.query(email).first()
# email.subject
# email.sender
# email.analysis

# Dict → data["subject"]
# Object → data.subject
