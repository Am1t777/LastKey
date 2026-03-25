# enum provides the standard Python enumeration base class
import enum
# datetime supplies the default timestamp for created_at / updated_at
from datetime import datetime

# SQLAlchemy column types; relationship links this model to related models
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

# Base is the declarative base all models inherit from
from app.database import Base


# SecretType categorises what kind of data this secret contains
# Using str + enum.Enum lets FastAPI/Pydantic serialize the value as a plain string
class SecretType(str, enum.Enum):
    password = "password"    # A username/password credential
    note = "note"            # A free-form text note
    document = "document"    # A text document (e.g., instructions, will excerpt)
    file = "file"            # Binary file content stored as base64


# Secret stores one encrypted item belonging to a user
class Secret(Base):
    # Maps to the "secrets" table in the database
    __tablename__ = "secrets"

    # Auto-incremented primary key
    id = Column(Integer, primary_key=True, index=True)
    # Foreign key linking this secret to the user who owns it
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Human-readable label shown in lists (never encrypted — intentional UX trade-off)
    title = Column(String, nullable=False)
    # AES-256-GCM ciphertext of the secret content, stored as a base64 string
    encrypted_content = Column(Text, nullable=False)
    # GCM nonce (initialisation vector) used during encryption, base64 — required for decryption
    encryption_iv = Column(String, nullable=False)
    # GCM authentication tag, base64 — validates ciphertext integrity during decryption
    encryption_tag = Column(String, nullable=False)
    # What kind of secret this is (password / note / document / file)
    secret_type = Column(Enum(SecretType), nullable=False, default=SecretType.note)
    # The AES encryption key, itself encrypted with the owner's Argon2id-derived key
    # Format: salt_b64:ciphertext_b64:iv_b64:tag_b64 — all four parts needed to recover the key
    owner_encrypted_key = Column(Text, nullable=False)
    # When the secret was first created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Automatically updated to the current time whenever the secret row is modified
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ORM relationship to the User model — lets us write secret.user to get the owner
    user = relationship("User", backref="secrets")
    # ORM relationship to SecretAssignment — cascade delete removes assignments when the secret is deleted
    assignments = relationship("SecretAssignment", back_populates="secret", cascade="all, delete-orphan")
