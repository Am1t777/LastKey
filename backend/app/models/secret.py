import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SecretType(str, enum.Enum):
    password = "password"
    note = "note"
    document = "document"
    file = "file"


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    encrypted_content = Column(Text, nullable=False)   # AES-256-GCM ciphertext (base64)
    encryption_iv = Column(String, nullable=False)     # GCM nonce (base64)
    encryption_tag = Column(String, nullable=False)    # GCM auth tag (base64)
    secret_type = Column(Enum(SecretType), nullable=False, default=SecretType.note)
    owner_encrypted_key = Column(Text, nullable=False)  # AES key encrypted with Argon2id(owner password), format: salt_b64:ct_b64:iv_b64:tag_b64
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="secrets")
    assignments = relationship("SecretAssignment", back_populates="secret", cascade="all, delete-orphan")
