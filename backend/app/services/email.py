
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings


def send_admin_verification_otp_email(
    recipient_email: str,
    otp: str,
) -> None:
    """Send the initial Company Admin email verification OTP."""

    if not settings.smtp_host or not settings.smtp_sender_email:
        raise RuntimeError("SMTP email configuration is incomplete.")

    message = EmailMessage()
    message["Subject"] = "Verify your PeopleSphere Admin account"
    message["From"] = formataddr(
        (settings.smtp_sender_name, settings.smtp_sender_email)
    )
    message["To"] = recipient_email

    message.set_content(
        f"""Welcome to PeopleSphere!

Your Company Admin account has been created.

Your email verification code is:

{otp}

This code:
- Expires in 5 minutes.
- Can only be used once.
- Must be entered to activate your account.

If you did not request this account, you can ignore this email.

PeopleSphere Team
"""
    )

    smtp_password = settings.smtp_password.get_secret_value()

    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, smtp_password)

            server.send_message(message)

    else:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as server:
            server.ehlo()

            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()

            if settings.smtp_username:
                server.login(settings.smtp_username, smtp_password)

            server.send_message(message)


# Legacy activation-link email function.
# Retain temporarily until the OTP workflow is fully integrated.

def send_admin_activation_email(
    recipient_email: str,
    activation_url: str,
) -> None:
    """Send the legacy Company Admin activation email."""

    if not settings.smtp_host or not settings.smtp_sender_email:
        raise RuntimeError("SMTP email configuration is incomplete.")

    message = EmailMessage()
    message["Subject"] = "Activate your PeopleSphere Admin account"
    message["From"] = formataddr(
        (settings.smtp_sender_name, settings.smtp_sender_email)
    )
    message["To"] = recipient_email

    message.set_content(
        f"""Welcome to PeopleSphere!

Use the following link to activate your account:

{activation_url}

If you did not request this account, you can ignore this email.
"""
    )

    smtp_password = settings.smtp_password.get_secret_value()

    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, smtp_password)
            server.send_message(message)

    else:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as server:
            server.ehlo()

            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()

            if settings.smtp_username:
                server.login(settings.smtp_username, smtp_password)

            server.send_message(message)
