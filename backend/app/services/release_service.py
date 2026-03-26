# secrets provides cryptographically secure random token generation
import secrets
# datetime and timedelta calculate token expiry timestamps
from datetime import datetime, timedelta

# SQLAlchemy session for all DB operations
from sqlalchemy.orm import Session

# App settings for configuring token expiry durations and URLs
from app.config import settings
# Beneficiary model — we query for all beneficiaries with assigned secrets
from app.models.beneficiary import Beneficiary
# SecretAssignment is used to count how many secrets each beneficiary will receive
from app.models.secret_assignment import SecretAssignment
# User model — the person whose switch has fired
from app.models.user import User
# log_audit records the release events in the audit log
from app.services.auth_service import log_audit
# Email helper to notify each beneficiary with their personal release link
from app.utils.email import send_beneficiary_release


# trigger_release is called when the verifier confirms the user's death/incapacitation
# It generates a unique time-limited link for each beneficiary and emails them
def trigger_release(db: Session, user: User, ip_address: str | None) -> None:
    # Record the exact UTC timestamp when the release was triggered
    now = datetime.utcnow()
    # Stamp the user record with the release time — used for display on the release page
    user.released_at = now
    # flush() sends the UPDATE to the DB without committing, making released_at available in this session
    db.flush()

    # Find all distinct beneficiaries who have at least one secret assigned to them from this user
    # We join through SecretAssignment to only include beneficiaries with actual secrets to receive
    beneficiaries = (
        db.query(Beneficiary)
        # Join Beneficiary to SecretAssignment on matching IDs
        .join(SecretAssignment, Beneficiary.id == SecretAssignment.beneficiary_id)
        # Only include beneficiaries belonging to this user
        .filter(Beneficiary.user_id == user.id)
        # distinct() prevents the same beneficiary appearing multiple times if they have multiple secrets
        .distinct()
        .all()
    )

    # Process each beneficiary independently so one email failure doesn't block the others
    for b in beneficiaries:
        # Generate a unique opaque token for this beneficiary's release link
        b.release_token = secrets.token_urlsafe(32)
        # Token expires after the configured number of days (default: 90 days)
        b.release_token_expires_at = now + timedelta(days=settings.RELEASE_TOKEN_EXPIRE_DAYS)
        # flush() so the token is available in the DB before we send the email (in case of crash between steps)
        db.flush()
        # Build the full URL the beneficiary will visit to access their secrets
        retrieval_url = f"{settings.FRONTEND_URL}/release/{b.release_token}"
        # Count how many secrets this beneficiary is receiving — shown in the email body
        secret_count = db.query(SecretAssignment).filter_by(beneficiary_id=b.id).count()
        try:
            # Send the release notification email with the personalized link
            send_beneficiary_release(b.name, b.email, user.name, retrieval_url, secret_count)
            # Log the successful email send for auditing
            log_audit(db, user.id, "release.notified", details=b.email, ip_address=ip_address)
        except Exception as e:
            # Email failure is non-fatal — log it and continue to the next beneficiary
            log_audit(db, user.id, "release.email_failed", details=f"{b.email}: {e}", ip_address=ip_address)

    # Commit all token assignments in one transaction after all emails have been attempted
    db.commit()
    # Log the overall release event with a count of how many beneficiaries were notified
    log_audit(db, user.id, "release.triggered", details=f"beneficiary_count={len(beneficiaries)}", ip_address=ip_address)
