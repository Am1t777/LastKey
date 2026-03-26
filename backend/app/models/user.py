# enum provides the standard Python enumeration base class
import enum
# datetime is used to set default timestamp values on columns
from datetime import datetime

# SQLAlchemy column types and the ORM declarative base
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Integer, String

# Base is the declarative base all models must inherit from
from app.database import Base


# SwitchStatus represents the four stages of the dead man's switch state machine
# Inheriting from both str and enum.Enum lets FastAPI serialize/deserialize the value as a plain string
class SwitchStatus(str, enum.Enum):
    active = "active"                      # User is checking in normally — no alerts sent
    reminder_sent = "reminder_sent"        # Check-in deadline missed; email reminder sent to user
    verifier_alerted = "verifier_alerted"  # Grace period expired; verifier has been contacted
    released = "released"                  # Verifier confirmed incapacitation; secrets released to beneficiaries


# User is the central model — every other model links back to it via user_id foreign keys
class User(Base):
    # Maps this Python class to the "users" table in the database
    __tablename__ = "users"

    # Primary key — auto-incremented integer; indexed automatically by SQLAlchemy
    id = Column(Integer, primary_key=True, index=True)
    # User's login email address — must be unique across the whole table
    email = Column(String, unique=True, index=True, nullable=False)
    # bcrypt hash of the user's password — the plaintext password is never stored
    password_hash = Column(String, nullable=False)
    # Display name used in email templates and the verifier confirmation check
    name = Column(String, nullable=False)
    # How many days the user has between required check-ins (default 30 days)
    check_in_interval_days = Column(Integer, default=30, nullable=False)
    # Timestamp of the user's most recent successful check-in; initialized to registration time
    last_check_in_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Soft-delete flag — False disables login without removing the account
    is_active = Column(Boolean, default=True, nullable=False)
    # When the account was created — used for auditing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Dead man's switch state machine columns:
    # Current stage of the switch — starts at "active" on registration
    switch_status = Column(SAEnum(SwitchStatus), default=SwitchStatus.active, nullable=False)
    # When the check-in reminder email was sent (NULL if never sent)
    reminder_sent_at = Column(DateTime, nullable=True)
    # When the trusted verifier was last contacted (NULL if never contacted)
    verifier_contacted_at = Column(DateTime, nullable=True)
    # One-time token embedded in the check-in email link — allows password-less check-in
    checkin_token = Column(String, unique=True, nullable=True)
    # When the check-in token expires — after this date the token is rejected
    checkin_token_expires_at = Column(DateTime, nullable=True)
    # Timestamp when secrets were released to beneficiaries (NULL until release)
    released_at = Column(DateTime, nullable=True)
