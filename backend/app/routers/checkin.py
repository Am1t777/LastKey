from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import SwitchStatus, User
from app.schemas.checkin import CheckinResponse, CheckinTokenRequest
from app.middleware.rate_limit import limiter
from app.services.auth_service import get_current_user, log_audit

router = APIRouter(prefix="/api/checkin", tags=["Check-in"])


def _do_checkin(user: User, db: Session, request: Request) -> CheckinResponse:
    user.last_check_in_at = datetime.utcnow()
    user.switch_status = SwitchStatus.active
    user.reminder_sent_at = None
    user.verifier_contacted_at = None
    user.checkin_token = None
    user.checkin_token_expires_at = None
    db.commit()
    log_audit(db, user.id, "checkin.completed", details="", ip_address=request.client.host)
    next_due = user.last_check_in_at + timedelta(days=user.check_in_interval_days)
    return CheckinResponse(message="Check-in successful. Your timer has been reset.", next_checkin_due=next_due)


@router.post("", response_model=CheckinResponse)
@limiter.limit("20/minute")
def checkin_by_token(
    body: CheckinTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    user = (
        db.query(User)
        .filter(
            User.checkin_token == body.token,
            User.checkin_token_expires_at > now,
            User.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired check-in token.",
        )
    return _do_checkin(user, db, request)


@router.post("/auth", response_model=CheckinResponse)
def checkin_authenticated(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _do_checkin(current_user, db, request)
