from datetime import datetime

from pydantic import BaseModel

from app.models.secret import SecretType


class ReleasedSecretItem(BaseModel):
    title: str
    secret_type: SecretType
    encrypted_content: str
    encryption_iv: str
    encryption_tag: str
    encrypted_key: str


class ReleaseResponse(BaseModel):
    deceased_name: str
    beneficiary_name: str
    released_at: datetime
    secrets: list[ReleasedSecretItem]
