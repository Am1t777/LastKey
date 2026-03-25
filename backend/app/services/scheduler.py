import secrets
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import SessionLocal
from app.models.trusted_verifier import TrustedVerifier
from app.models.user import SwitchStatus, User
from app.services.auth_service import log_audit
from app.utils.email import (
    send_checkin_reminder,
    send_no_verifier_warning,
    send_verifier_alert,
)

scheduler = AsyncIOScheduler(timezone="UTC")


async def run_checkin_job() -> None:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        users = db.query(User).filter(User.is_active == True).all()  # noqa: E712
        for user in users:
            deadline = user.last_check_in_at + timedelta(days=user.check_in_interval_days)
            grace_end = deadline + timedelta(days=settings.GRACE_PERIOD_DAYS)

            if now <= deadline:
                # User is current — reset any stale switch state
                if user.switch_status != SwitchStatus.active:
                    user.switch_status = SwitchStatus.active
                    user.reminder_sent_at = None
                    user.verifier_contacted_at = None
                    db.commit()
                continue

            if deadline < now <= grace_end:
                # Overdue but within grace period — send one reminder
                if user.switch_status == SwitchStatus.active:
                    token = secrets.token_urlsafe(32)
                    expires = now + timedelta(days=settings.CHECKIN_TOKEN_EXPIRE_DAYS)
                    user.checkin_token = token
                    user.checkin_token_expires_at = expires
                    user.switch_status = SwitchStatus.reminder_sent
                    user.reminder_sent_at = now
                    db.commit()
                    checkin_url = f"{settings.BASE_URL}/api/checkin?token={token}"
                    try:
                        send_checkin_reminder(user.name, user.email, checkin_url)
                    except Exception:
                        pass  # Email failure must not crash the job
                    log_audit(db, user.id, "checkin.reminder_sent", details=user.email, ip_address="scheduler")
                # Already reminded → do nothing until grace period ends
                continue

            # Grace period expired
            if user.switch_status in (SwitchStatus.active, SwitchStatus.reminder_sent):
                verifier: TrustedVerifier | None = (
                    db.query(TrustedVerifier).filter(TrustedVerifier.user_id == user.id).first()
                )
                if not verifier:
                    try:
                        send_no_verifier_warning(user.name, user.email)
                    except Exception:
                        pass
                    log_audit(db, user.id, "checkin.no_verifier_warning", details=user.email, ip_address="scheduler")
                    continue

                # Refresh tokens and contact verifier
                verifier.verification_token = secrets.token_urlsafe(32)
                verifier.denial_token = secrets.token_urlsafe(32)
                verifier.contacted_at = now
                verifier.has_confirmed = False
                verifier.has_denied = False
                user.switch_status = SwitchStatus.verifier_alerted
                user.verifier_contacted_at = now
                db.commit()

                confirm_url = f"{settings.BASE_URL}/api/verify/{verifier.verification_token}/confirm"
                deny_url = f"{settings.BASE_URL}/api/verify/{verifier.denial_token}/deny"
                try:
                    send_verifier_alert(verifier.name, verifier.email, user.name, confirm_url, deny_url)
                except Exception:
                    pass
                log_audit(db, user.id, "checkin.verifier_alerted", details=verifier.email, ip_address="scheduler")
            # If already verifier_alerted → do nothing (Step 9 handles release)
    finally:
        db.close()
