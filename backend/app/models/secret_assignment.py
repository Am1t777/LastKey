# SQLAlchemy column types for defining the table schema
from sqlalchemy import Column, ForeignKey, Integer, Text
# relationship lets us navigate between related ORM objects in Python
from sqlalchemy.orm import relationship

# Base is the declarative base all models inherit from
from app.database import Base


# SecretAssignment is the join table that connects a Secret to a Beneficiary
# It stores the AES encryption key re-encrypted specifically for that beneficiary
# This is the core of the zero-knowledge key distribution scheme:
#   one AES key per secret → encrypted separately for each beneficiary with their RSA public key
class SecretAssignment(Base):
    # Maps to the "secret_assignments" table in the database
    __tablename__ = "secret_assignments"

    # Auto-incremented primary key
    id = Column(Integer, primary_key=True, index=True)
    # Foreign key to the secret being assigned — deleting the secret cascades here
    secret_id = Column(Integer, ForeignKey("secrets.id"), nullable=False)
    # Foreign key to the beneficiary who will receive this secret
    beneficiary_id = Column(Integer, ForeignKey("beneficiaries.id"), nullable=False)
    # The AES-256 key that decrypts the secret content, encrypted with the beneficiary's RSA public key
    # Stored as base64 — only the beneficiary (holding the private key) can decrypt it
    encrypted_key = Column(Text, nullable=False)

    # ORM relationship to Secret — lets us write assignment.secret to get the parent Secret
    secret = relationship("Secret", back_populates="assignments")
    # ORM relationship to Beneficiary — lets us write assignment.beneficiary to get the Beneficiary
    beneficiary = relationship("Beneficiary", backref="assignments")
