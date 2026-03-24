from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SecretAssignment(Base):
    __tablename__ = "secret_assignments"

    id = Column(Integer, primary_key=True, index=True)
    secret_id = Column(Integer, ForeignKey("secrets.id"), nullable=False)
    beneficiary_id = Column(Integer, ForeignKey("beneficiaries.id"), nullable=False)
    encrypted_key = Column(Text, nullable=False)  # AES key encrypted with beneficiary's RSA public key (base64)

    secret = relationship("Secret", back_populates="assignments")
    beneficiary = relationship("Beneficiary", backref="assignments")
