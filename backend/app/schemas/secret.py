from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.secret import SecretType


class SecretCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)          # plaintext — encrypted server-side
    secret_type: SecretType = SecretType.note
    password: str = Field(min_length=8)         # used to derive Argon2id owner key
    beneficiary_ids: list[int] = []             # optional: assign at creation time


class SecretUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    secret_type: SecretType | None = None
    password: str | None = None                 # required when content is being changed


class SecretAssignRequest(BaseModel):
    beneficiary_id: int
    password: str = Field(min_length=8)         # re-derives owner key to decrypt + re-encrypt AES key


class SecretResponse(BaseModel):
    id: int
    title: str
    secret_type: SecretType
    encrypted_content: str
    encryption_iv: str
    encryption_tag: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SecretListItem(BaseModel):
    id: int
    title: str
    secret_type: SecretType
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SecretListResponse(BaseModel):
    items: list[SecretListItem]
    total: int
    page: int
    page_size: int
