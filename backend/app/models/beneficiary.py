from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    public_key = Column(Text, nullable=True)  # RSA public key (PEM), set when beneficiary registers
    release_token = Column(String, unique=True, nullable=True)
    release_token_expires_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="beneficiaries")
