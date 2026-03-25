from datetime import datetime

from pydantic import BaseModel, Field


class CheckinTokenRequest(BaseModel):
    token: str = Field(min_length=1)


class CheckinResponse(BaseModel):
    message: str
    next_checkin_due: datetime
