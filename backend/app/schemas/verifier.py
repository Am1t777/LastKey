from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VerifierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class VerifierResponse(BaseModel):
    id: int
    name: str
    email: str
    has_confirmed: bool
    has_denied: bool
    model_config = ConfigDict(from_attributes=True)


class VerifierConfirmRequest(BaseModel):
    confirmation_text: str = Field(min_length=1)  # must match user.name (case-insensitive)


class VerifierActionResponse(BaseModel):
    message: str
    action: str  # "confirmed" | "denied"
