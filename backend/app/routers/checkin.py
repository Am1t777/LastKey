# datetime and timedelta compute the next check-in due date returned in the response
from datetime import datetime, timedelta

# FastAPI routing, dependency injection, HTTP exceptions, request object, and status codes
from fastapi import APIRouter, Depends, HTTPException, Request, status
# SQLAlchemy session for DB access
from sqlalchemy.orm import Session

# Database session dependency
from app.database import get_db
# User ORM model and SwitchStatus enum for resetting the state machine
from app.models.user import SwitchStatus, User
# Pydantic schemas for request and response bodies
from app.schemas.checkin import CheckinResponse, CheckinTokenRequest
# Rate limiter — applied to the token-based endpoint to prevent token brute-forcing
from app.middleware.rate_limit import limiter
# JWT validation and audit logging
from app.services.auth_service import get_current_user, log_audit

# Group both check-in endpoints under /api/checkin with the "Check-in" tag
router = APIRouter(prefix="/api/checkin", tags=["Check-in"])


# _do_checkin is the shared logic that resets the dead man's switch for a user
def _do_checkin(user: User, db: Session, request: Request) -> CheckinResponse:
    # Update the last check-in timestamp to right now
    user.last_check_in_at = datetime.utcnow()
    # Reset the switch status to "active" — the user is confirmed alive
    user.switch_status = SwitchStatus.active
    # Clear the reminder timestamp — the current reminder cycle is over
    user.reminder_sent_at = None
    # Clear the verifier contact timestamp — no longer relevant
    user.verifier_contacted_at = None
    # Invalidate the one-time check-in token so the email link cannot be reused
    user.checkin_token = None
    user.checkin_token_expires_at = None
    # Persist all the above changes to the database
    db.commit()
    # Write an audit log entry for this check-in
    log_audit(db, user.id, "checkin.completed", details="", ip_address=request.client.host)
    # Calculate when the next check-in will be due for display in the UI
    next_due = user.last_check_in_at + timedelta(days=user.check_in_interval_days)
    return CheckinResponse(message="Check-in successful. Your timer has been reset.", next_checkin_due=next_due)


# POST /api/checkin — token-based (password-less) check-in via email link
@router.post("", response_model=CheckinResponse)
# Rate-limited to prevent automated token brute-forcing
@limiter.limit("20/minute")
def checkin_by_token(
    body: CheckinTokenRequest,  # Body contains the one-time token from the email link
    request: Request,
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    # Look up the user whose checkin_token matches the provided value
    # Also verify the token hasn't expired and the account is active
    user = (
        db.query(User)
        .filter(
            User.checkin_token == body.token,              # Token must match exactly
            User.checkin_token_expires_at > now,           # Token must not be expired
            User.is_active == True,  # noqa: E712          # Account must be active
        )
        .first()
    )
    if not user:
        # Either the token doesn't exist, has expired, or belongs to a deactivated account
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired check-in token.",
        )
    # Token is valid — perform the check-in
    return _do_checkin(user, db, request)


# POST /api/checkin/auth — authenticated check-in (user is already logged in via JWT)
@router.post("/auth", response_model=CheckinResponse)
def checkin_authenticated(
    request: Request,
    # JWT-authenticated — this endpoint requires a valid access token
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # The user is already identified via JWT — just perform the check-in
    return _do_checkin(current_user, db, request)
