# smtplib provides a Python SMTP client for sending email over the network
import smtplib
# MIMEMultipart and MIMEText build the MIME email message structure
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# App settings for SMTP credentials and the From address
from app.config import settings


# send_email is the low-level SMTP delivery function used by all template helpers below
def send_email(to: str, subject: str, html: str) -> None:
    # Create an "alternative" MIME message — allows clients to render HTML or plain text
    msg = MIMEMultipart("alternative")
    # Set the email subject line
    msg["Subject"] = subject
    # Set the sending address from config
    msg["From"] = settings.EMAIL_FROM
    # Set the recipient address
    msg["To"] = to
    # Attach the HTML body — "html" tells the mail client to render it as markup
    msg.attach(MIMEText(html, "html"))

    # Open a new SMTP connection to the configured mail server
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        # ehlo() introduces the client to the server (required before STARTTLS)
        server.ehlo()
        # Upgrade the connection to TLS for encrypted transport
        server.starttls()
        # Only authenticate if SMTP credentials are configured (allows unauthenticated relay in dev)
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        # Send the email — from_addr and to_addrs control SMTP envelope; msg provides headers + body
        server.sendmail(settings.EMAIL_FROM, to, msg.as_string())


# _btn is a helper that renders an HTML button/link for use in email templates
# Returns a raw HTML <a> tag styled as a colored button
def _btn(url: str, label: str, color: str = "#2563eb") -> str:
    return (
        f'<a href="{url}" style="display:inline-block;padding:12px 24px;'
        f"background:{color};color:#fff;text-decoration:none;border-radius:6px;"
        f'font-weight:bold;font-size:15px;">{label}</a>'
    )


# _layout wraps an email body in a consistent HTML shell with white card on grey background
def _layout(body: str) -> str:
    return f"""<!DOCTYPE html>
<html><body style="font-family:sans-serif;background:#f4f4f4;padding:32px;">
<div style="max-width:520px;margin:auto;background:#fff;border-radius:10px;padding:32px;">
{body}
<hr style="margin:32px 0;border:none;border-top:1px solid #eee;">
<p style="color:#999;font-size:12px;">This email was sent by LastKey — Digital Inheritance Vault.</p>
</div></body></html>"""


# send_checkin_reminder emails the user when they have missed their check-in deadline
# The email contains a one-click check-in link with an embedded token
def send_checkin_reminder(user_name: str, user_email: str, checkin_url: str) -> None:
    html = _layout(f"""
<h2 style="color:#1e293b;">Time to check in, {user_name}</h2>
<p style="color:#475569;">Your LastKey check-in is overdue. Please confirm you are well by clicking the button below.</p>
<p style="color:#475569;">If you do not check in within 7 days, your trusted verifier will be contacted.</p>
<p style="margin:28px 0;">{_btn(checkin_url, "Check In Now")}</p>
<p style="color:#94a3b8;font-size:13px;">If you did not set up this account, you can safely ignore this email.</p>
""")
    # Send the assembled HTML email to the user
    send_email(user_email, "LastKey — Please check in", html)


# send_verifier_alert emails the trusted verifier when the user's grace period has expired
# The email contains two action buttons: one to confirm incapacitation, one to deny it
def send_verifier_alert(
    verifier_name: str,    # The verifier's name — used in the email greeting
    verifier_email: str,   # Where to send the email
    user_name: str,        # The name of the user being verified
    confirm_url: str,      # URL for the "confirm incapacitation" action (red button)
    deny_url: str,         # URL for the "they are alive" action (green button)
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
    # Send the alert email to the verifier
    send_email(verifier_email, f"LastKey — Verification needed for {user_name}", html)


# send_beneficiary_release emails a beneficiary to notify them that secrets have been released
# The email contains their personal retrieval link (valid for 90 days)
def send_beneficiary_release(
    beneficiary_name: str,   # The beneficiary's name for the greeting
    beneficiary_email: str,  # Where to send the notification
    deceased_name: str,      # The name of the person who passed away
    retrieval_url: str,      # The beneficiary's unique URL to access their secrets
    secret_count: int,       # How many secrets they are receiving
) -> None:
    html = _layout(f"""
<h2 style="color:#dc2626;">Important notice regarding {deceased_name}</h2>
<p style="color:#475569;">Hello {beneficiary_name},</p>
<p style="color:#475569;">
  We are sorry to inform you that <strong>{deceased_name}</strong> has passed away or become incapacitated.
  They designated you as a beneficiary on LastKey — Digital Inheritance Vault.
</p>
<p style="color:#475569;">
  <strong>{secret_count}</strong> secret(s) have been released to you. Click the button below to access them.
</p>
<p style="margin:28px 0;">{_btn(retrieval_url, "Access My Secrets", "#dc2626")}</p>
<p style="color:#94a3b8;font-size:13px;">
  If the button does not work, copy and paste this link into your browser:<br>
  <a href="{retrieval_url}" style="color:#94a3b8;">{retrieval_url}</a>
</p>
<p style="color:#94a3b8;font-size:13px;">
  This link will expire in 90 days. Please save the contents securely before then.
</p>
""")
    # Send the release notification to the beneficiary
    send_email(beneficiary_email, f"LastKey — {deceased_name} has designated you as a beneficiary", html)


# send_no_verifier_warning emails the user when their grace period expired but no verifier is set
# Without a verifier the system cannot escalate, so this is an urgent warning to the user themselves
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
    # Send the urgent warning to the user's own email address
    send_email(user_email, "LastKey — URGENT: No trusted verifier configured", html)
