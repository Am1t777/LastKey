# SQLAlchemy column types for defining the table schema
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
# relationship lets us navigate between related ORM objects in Python
from sqlalchemy.orm import relationship

# Base is the declarative base all models inherit from
from app.database import Base


# TrustedVerifier is the person the user trusts to confirm their death/incapacitation
# One user can have at most one trusted verifier at a time
class TrustedVerifier(Base):
    # Maps to the "trusted_verifiers" table in the database
    __tablename__ = "trusted_verifiers"

    # Auto-incremented primary key
    id = Column(Integer, primary_key=True, index=True)
    # Foreign key linking this verifier record to the user they are watching over
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Display name of the verifier — used in email salutations
    name = Column(String, nullable=False)
    # Email address where the verification request is sent when the switch fires
    email = Column(String, nullable=False)
    # Secret token embedded in the "confirm incapacitation" email link
    # Unique and opaque so it cannot be guessed by a third party
    verification_token = Column(String, unique=True, nullable=False)
    # True once the verifier clicks the "confirm" link and the name-match check passes
    has_confirmed = Column(Boolean, default=False, nullable=False)
    # Secret token embedded in the "they are alive" (deny) email link
    # A separate token from verification_token to avoid accidental confirmation
    denial_token = Column(String, unique=True, nullable=True)
    # True once the verifier clicks the "deny" link (user is still alive)
    has_denied = Column(Boolean, default=False, nullable=False)
    # Timestamp when the verifier was last sent an alert email
    contacted_at = Column(DateTime, nullable=True)

    # ORM relationship to User — lets us access v.user to get the user being verified
    user = relationship("User", backref="trusted_verifier")
