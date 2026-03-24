from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BeneficiaryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class BeneficiaryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None


class BeneficiaryResponse(BaseModel):
    id: int
    name: str
    email: str
    has_key: bool   # computed from public_key is not None — public key itself is never exposed
    model_config = ConfigDict(from_attributes=True)


class BeneficiaryWithKeyResponse(BeneficiaryResponse):
    private_key_pem: str    # returned exactly once on generate-key endpoint; owner must deliver to beneficiary


class SecretAssignmentInfo(BaseModel):
    id: int
    secret_id: int
    beneficiary_id: int
    model_config = ConfigDict(from_attributes=True)
