# datetime supplies the default timestamp for created_at
from datetime import datetime

# SQLAlchemy column types for defining the table schema
from sqlalchemy import Column, DateTime, Integer, String, Text

# Base is the declarative base all models inherit from
from app.database import Base


# AuditLog records every sensitive action in the system for security and forensic purposes
# It provides an immutable trail of who did what, when, and from where
class AuditLog(Base):
    # Maps to the "audit_logs" table in the database
    __tablename__ = "audit_logs"

    # Auto-incremented primary key — used to establish chronological order alongside created_at
    id = Column(Integer, primary_key=True, index=True)
    # The user who performed the action — nullable because some events happen before auth
    # (e.g., a failed login attempt has no authenticated user yet)
    user_id = Column(Integer, nullable=True)
    # Dot-namespaced event name, e.g. "user.login", "secret.create", "checkin.reminder_sent"
    # Using a consistent naming convention makes log querying and alerting easier
    action = Column(String, nullable=False)
    # Optional JSON string with additional context about the event (email, secret title, etc.)
    details = Column(Text, nullable=True)
    # The IP address of the client who triggered this action — used for forensics
    # "scheduler" is used as a synthetic IP when the background job creates entries
    ip_address = Column(String, nullable=True)
    # Exact UTC timestamp when the event occurred — auto-set to now on insert
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
