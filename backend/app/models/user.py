import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Integer, String

from app.database import Base


class SwitchStatus(str, enum.Enum):
    active = "active"
    reminder_sent = "reminder_sent"
    verifier_alerted = "verifier_alerted"
    released = "released"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    check_in_interval_days = Column(Integer, default=30, nullable=False)
    last_check_in_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Dead man's switch state machine
    switch_status = Column(SAEnum(SwitchStatus), default=SwitchStatus.active, nullable=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    verifier_contacted_at = Column(DateTime, nullable=True)
    checkin_token = Column(String, unique=True, nullable=True)
    checkin_token_expires_at = Column(DateTime, nullable=True)
