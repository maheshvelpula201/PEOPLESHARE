
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()

JWT_ALGORITHM = "HS256"


# Password security

def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


# Email OTP security

def generate_email_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_email_otp(otp: str) -> str:
    secret = settings.email_otp_hmac_secret.get_secret_value()

    if not secret:
        raise RuntimeError("EMAIL_OTP_HMAC_SECRET is not configured.")

    return hmac.new(
        secret.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_email_otp(otp: str, stored_hash: str) -> bool:
    candidate_hash = hash_email_otp(otp)
    return hmac.compare_digest(candidate_hash, stored_hash)


# JWT access tokens

def create_access_token(user) -> str:
    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user.id),
        "company_id": user.company_id,
        "role": user.role.value,
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "company_id", "role", "type", "exp"]},
    )


# Refresh token security

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# Legacy activation-link security (temporary)

def generate_admin_activation_token() -> str:
    return secrets.token_urlsafe(32)


def hash_admin_activation_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
