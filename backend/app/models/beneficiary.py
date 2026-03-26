# SQLAlchemy column types for defining the table schema
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
# relationship lets us navigate between related ORM objects in Python code
from sqlalchemy.orm import relationship

# Base is the declarative base all models inherit from
from app.database import Base


# Beneficiary represents a person the user wants to receive their secrets after death/incapacitation
class Beneficiary(Base):
    # Maps to the "beneficiaries" table in the database
    __tablename__ = "beneficiaries"

    # Auto-incremented primary key
    id = Column(Integer, primary_key=True, index=True)
    # Foreign key — links this beneficiary to the user who added them
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Display name of the beneficiary — shown in emails and the UI
    name = Column(String, nullable=False)
    # Email address where the release notification will be sent
    email = Column(String, nullable=False)
    # RSA-2048 public key in PEM format — stored here after key generation
    # The matching private key is given to the beneficiary and NEVER stored server-side
    # NULL until the user clicks "Generate Key" for this beneficiary
    public_key = Column(Text, nullable=True)
    # One-time token embedded in the beneficiary's release email link
    # NULL until the dead man's switch fires and release is triggered
    release_token = Column(String, unique=True, nullable=True)
    # Expiry date for the release token — after this the link no longer works
    release_token_expires_at = Column(DateTime, nullable=True)

    # ORM relationship to User — lets us access b.user to get the owning user
    user = relationship("User", backref="beneficiaries")
