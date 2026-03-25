import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def send_email(to: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to, msg.as_string())


def _btn(url: str, label: str, color: str = "#2563eb") -> str:
    return (
        f'<a href="{url}" style="display:inline-block;padding:12px 24px;'
        f"background:{color};color:#fff;text-decoration:none;border-radius:6px;"
        f'font-weight:bold;font-size:15px;">{label}</a>'
    )


def _layout(body: str) -> str:
    return f"""<!DOCTYPE html>
<html><body style="font-family:sans-serif;background:#f4f4f4;padding:32px;">
<div style="max-width:520px;margin:auto;background:#fff;border-radius:10px;padding:32px;">
{body}
<hr style="margin:32px 0;border:none;border-top:1px solid #eee;">
<p style="color:#999;font-size:12px;">This email was sent by LastKey — Digital Inheritance Vault.</p>
</div></body></html>"""


def send_checkin_reminder(user_name: str, user_email: str, checkin_url: str) -> None:
    html = _layout(f"""
<h2 style="color:#1e293b;">Time to check in, {user_name}</h2>
<p style="color:#475569;">Your LastKey check-in is overdue. Please confirm you are well by clicking the button below.</p>
<p style="color:#475569;">If you do not check in within 7 days, your trusted verifier will be contacted.</p>
<p style="margin:28px 0;">{_btn(checkin_url, "Check In Now")}</p>
<p style="color:#94a3b8;font-size:13px;">If you did not set up this account, you can safely ignore this email.</p>
""")
    send_email(user_email, "LastKey — Please check in", html)


def send_verifier_alert(
    verifier_name: str,
    verifier_email: str,
    user_name: str,
    confirm_url: str,
    deny_url: str,
) -> None:
    html = _layout(f"""
<h2 style="color:#1e293b;">Verification request for {user_name}</h2>
<p style="color:#475569;">Hello {verifier_name},</p>
<p style="color:#475569;">
  You have been designated as the trusted verifier for <strong>{user_name}</strong> on LastKey.
  They have missed their scheduled check-in and we need your help to verify their status.
</p>
<p style="color:#475569;">Please choose one of the options below:</p>
<p style="margin:28px 0;">
  {_btn(confirm_url, "Confirm incapacitation", "#dc2626")}
  &nbsp;&nbsp;
  {_btn(deny_url, "They are alive and well", "#16a34a")}
</p>
<p style="color:#94a3b8;font-size:13px;">
  To confirm, you will be asked to type the person's full name as a safety check.
</p>
""")
    send_email(verifier_email, f"LastKey — Verification needed for {user_name}", html)


def send_no_verifier_warning(user_name: str, user_email: str) -> None:
    html = _layout(f"""
<h2 style="color:#dc2626;">Action required: No trusted verifier set</h2>
<p style="color:#475569;">Hello {user_name},</p>
<p style="color:#475569;">
  Your LastKey check-in grace period has expired, but <strong>you have not set a trusted verifier</strong>.
  Without a verifier, your beneficiaries cannot be notified in an emergency.
</p>
<p style="color:#475569;">Please log in and add a trusted verifier as soon as possible.</p>
""")
    send_email(user_email, "LastKey — URGENT: No trusted verifier configured", html)
