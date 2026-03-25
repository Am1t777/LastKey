from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user, log_audit

router = APIRouter(prefix="/api/settings", tags=["Settings"])

class IntervalUpdate(BaseModel):
    days: int = Field(..., ge=1, le=365)

class IntervalResponse(BaseModel):
    check_in_interval_days: int

@router.patch("/interval", response_model=IntervalResponse)
def update_interval(
    body: IntervalUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.check_in_interval_days = body.days
    db.commit()
    db.refresh(current_user)
    log_audit(db, current_user.id, "settings.interval_updated", details=str(body.days), ip_address=request.client.host)
    return IntervalResponse(check_in_interval_days=current_user.check_in_interval_days)
