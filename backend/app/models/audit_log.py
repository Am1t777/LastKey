from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)   # nullable — some events may be pre-auth
    action = Column(String, nullable=False)    # e.g. "user.login", "secret.create"
    details = Column(Text, nullable=True)      # JSON string with extra context
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
