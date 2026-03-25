import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models.beneficiary import Beneficiary
from app.models.secret_assignment import SecretAssignment
from app.models.user import User
from app.services.auth_service import log_audit
from app.utils.email import send_beneficiary_release


def trigger_release(db: Session, user: User, ip_address: str | None) -> None:
    now = datetime.utcnow()
    user.released_at = now
    db.flush()

    beneficiaries = (
        db.query(Beneficiary)
        .join(SecretAssignment, Beneficiary.id == SecretAssignment.beneficiary_id)
        .filter(Beneficiary.user_id == user.id)
        .distinct()
        .all()
    )

    for b in beneficiaries:
        b.release_token = secrets.token_urlsafe(32)
        b.release_token_expires_at = now + timedelta(days=settings.RELEASE_TOKEN_EXPIRE_DAYS)
        db.flush()
        retrieval_url = f"{settings.FRONTEND_URL}/release/{b.release_token}"
        secret_count = db.query(SecretAssignment).filter_by(beneficiary_id=b.id).count()
        try:
            send_beneficiary_release(b.name, b.email, user.name, retrieval_url, secret_count)
            log_audit(db, user.id, "release.notified", details=b.email, ip_address=ip_address)
        except Exception as e:
            log_audit(db, user.id, "release.email_failed", details=f"{b.email}: {e}", ip_address=ip_address)

    db.commit()
    log_audit(db, user.id, "release.triggered", details=f"beneficiary_count={len(beneficiaries)}", ip_address=ip_address)
