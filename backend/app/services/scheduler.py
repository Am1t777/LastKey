# secrets generates cryptographically secure random tokens for check-in links
import secrets
# datetime and timedelta calculate deadlines and expiry timestamps
from datetime import datetime, timedelta

# AsyncIOScheduler runs background jobs on an asyncio event loop without blocking requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# App settings for grace period, token expiry, and base URL configuration
from app.config import settings
# SessionLocal creates a new DB session for use inside the background job
# (we can't use FastAPI's get_db() dependency here because there's no request context)
from app.database import SessionLocal
# TrustedVerifier model — queried when the grace period expires
from app.models.trusted_verifier import TrustedVerifier
# User and SwitchStatus — we iterate over all active users and advance their state machine
from app.models.user import SwitchStatus, User
# log_audit writes switch-state events to the audit log
from app.services.auth_service import log_audit
# Email helpers — each sends a different type of notification
from app.utils.email import (
    send_checkin_reminder,    # Email to the user when they miss their check-in deadline
    send_no_verifier_warning, # Email to the user if grace period expired but no verifier is set
    send_verifier_alert,      # Email to the verifier when grace period expires with a verifier set
)

# Create the APScheduler instance using asyncio mode so it plays well with FastAPI's event loop
scheduler = AsyncIOScheduler(timezone="UTC")


# run_checkin_job is the daily cron function that advances the dead man's switch state machine
# It is registered to run every day at 02:00 UTC (low-traffic time)
async def run_checkin_job() -> None:
    # Open a dedicated DB session for this background job
    db = SessionLocal()
    try:
        # Get the current UTC time once so all comparisons in this run are consistent
        now = datetime.utcnow()
        # Load all active (non-deleted) user accounts — inactive accounts are ignored
        users = db.query(User).filter(User.is_active == True).all()  # noqa: E712
        for user in users:
            # Calculate when this user's check-in was due
            deadline = user.last_check_in_at + timedelta(days=user.check_in_interval_days)
            # Calculate the end of the grace period (deadline + 7 days by default)
            grace_end = deadline + timedelta(days=settings.GRACE_PERIOD_DAYS)

            if now <= deadline:
                # User is current — reset any stale switch state that may have been set
                # (e.g., user checked in after a reminder was sent but before grace period ended)
                if user.switch_status != SwitchStatus.active:
                    # Reset all switch fields back to their default "all-clear" state
                    user.switch_status = SwitchStatus.active
                    user.reminder_sent_at = None
                    user.verifier_contacted_at = None
                    db.commit()
                # Move on to the next user — nothing to do
                continue

            if deadline < now <= grace_end:
                # User missed their deadline but is still within the 7-day grace period
                if user.switch_status == SwitchStatus.active:
                    # Generate a one-time check-in token so the user can check in via email link
                    token = secrets.token_urlsafe(32)
                    # Token expires after the configured number of days
                    expires = now + timedelta(days=settings.CHECKIN_TOKEN_EXPIRE_DAYS)
                    # Store the token and its expiry on the user record
                    user.checkin_token = token
                    user.checkin_token_expires_at = expires
                    # Advance the switch to "reminder sent" state
                    user.switch_status = SwitchStatus.reminder_sent
                    # Record when the reminder was sent for visibility in the admin/audit log
                    user.reminder_sent_at = now
                    db.commit()
                    # Build the one-click check-in URL containing the token
                    checkin_url = f"{settings.BASE_URL}/api/checkin?token={token}"
                    try:
                        # Send the reminder email — failure is swallowed so the job continues
                        send_checkin_reminder(user.name, user.email, checkin_url)
                    except Exception:
                        pass  # Email failure must not crash the job
                    # Write an audit entry so we can see when reminders were sent
                    log_audit(db, user.id, "checkin.reminder_sent", details=user.email, ip_address="scheduler")
                # If reminder was already sent this cycle, do nothing until grace period ends
                continue

            # Grace period has expired — time to escalate
            if user.switch_status in (SwitchStatus.active, SwitchStatus.reminder_sent):
                # Look up whether the user has a trusted verifier set
                verifier: TrustedVerifier | None = (
                    db.query(TrustedVerifier).filter(TrustedVerifier.user_id == user.id).first()
                )
                if not verifier:
                    # No verifier means we cannot escalate — warn the user and move on
                    try:
                        send_no_verifier_warning(user.name, user.email)
                    except Exception:
                        pass
                    # Record that we sent the no-verifier warning
                    log_audit(db, user.id, "checkin.no_verifier_warning", details=user.email, ip_address="scheduler")
                    # Cannot proceed without a verifier — skip to next user
                    continue

                # Refresh tokens so old links (from a previous alert cycle) no longer work
                verifier.verification_token = secrets.token_urlsafe(32)  # new confirm token
                verifier.denial_token = secrets.token_urlsafe(32)         # new deny token
                # Record when the verifier was contacted this time
                verifier.contacted_at = now
                # Reset confirmation/denial flags in case this is a repeat alert
                verifier.has_confirmed = False
                verifier.has_denied = False
                # Advance the user's switch to "verifier alerted" state
                user.switch_status = SwitchStatus.verifier_alerted
                # Record when the verifier was contacted for auditing and display
                user.verifier_contacted_at = now
                db.commit()

                # Build the two action URLs for the verifier's email
                confirm_url = f"{settings.BASE_URL}/api/verify/{verifier.verification_token}/confirm"
                deny_url = f"{settings.BASE_URL}/api/verify/{verifier.denial_token}/deny"
                try:
                    # Email the verifier with both the confirm and deny buttons
                    send_verifier_alert(verifier.name, verifier.email, user.name, confirm_url, deny_url)
                except Exception:
                    pass
                # Write an audit entry recording that the verifier was alerted
                log_audit(db, user.id, "checkin.verifier_alerted", details=verifier.email, ip_address="scheduler")
            # If switch is already "verifier_alerted" we wait — release is triggered by the verifier's response
    finally:
        # Always close the session to return the DB connection to the pool
        db.close()
