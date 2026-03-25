from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class TrustedVerifier(Base):
    __tablename__ = "trusted_verifiers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    verification_token = Column(String, unique=True, nullable=False)
    has_confirmed = Column(Boolean, default=False, nullable=False)
    denial_token = Column(String, unique=True, nullable=True)
    has_denied = Column(Boolean, default=False, nullable=False)
    contacted_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="trusted_verifier")
