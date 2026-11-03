
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_email_otp,
    generate_refresh_token,
    hash_email_otp,
    hash_refresh_token,
    verify_email_otp,
    verify_password,
)
from app.models.email_verification_otp import (
    EmailVerificationOTP,
    OTPDeliveryStatus,
)
from app.models.refresh_session import RefreshSession
from app.models.user import (
    AccountOrigin,
    AccountStatus,
    User,
    UserRole,
)
from app.schemas.auth import (
    AuthTokenResponse,
    EmailVerificationRequest,
    LoginRequest,
    ResendVerificationRequest,
)
from app.services.email import send_admin_verification_otp_email


logger = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:

    @staticmethod
    def _build_token_response(
        user: User,
        refresh_token: str,
    ) -> AuthTokenResponse:
        return AuthTokenResponse(
            access_token=create_access_token(user),
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user_id=user.id,
            company_id=user.company_id,
            email=user.normalized_email,
            role=user.role.value,
        )

    @staticmethod
    def _create_refresh_session(
        db: Session,
        user: User,
        raw_token: str,
        now: datetime,
    ) -> None:
        session = RefreshSession(
            company_id=user.company_id,
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=now + timedelta(
                days=settings.refresh_token_expire_days
            ),
        )
        db.add(session)

    # --------------------------------------------------
    # EMAIL OTP VERIFICATION
    # --------------------------------------------------

    @staticmethod
    def verify_registration_email(
        db: Session,
        request: EmailVerificationRequest,
    ) -> AuthTokenResponse:

        now = datetime.now(timezone.utc)

        try:
            user = db.scalar(
                select(User)
                .where(
                    User.company_id == request.company_id,
                    User.normalized_email == str(request.email).lower(),
                )
                .with_for_update()
            )

            if (
                user is None
                or user.role != UserRole.COMPANY_ADMIN
                or user.account_origin != AccountOrigin.REGISTRATION
                or user.account_status != AccountStatus.PENDING_ACTIVATION
            ):
                raise AuthError(
                    "Invalid or unavailable verification request.",
                    400,
                )

            otp_record = db.scalar(
                select(EmailVerificationOTP)
                .where(
                    EmailVerificationOTP.company_id == user.company_id,
                    EmailVerificationOTP.user_id == user.id,
                    EmailVerificationOTP.consumed_at.is_(None),
                    EmailVerificationOTP.invalidated_at.is_(None),
                )
                .order_by(EmailVerificationOTP.created_at.desc())
                .with_for_update()
            )

            if otp_record is None:
                raise AuthError(
                    "No active verification code exists. Please request a new code.",
                    400,
                )

            if otp_record.delivery_status != OTPDeliveryStatus.SENT:
                raise AuthError(
                    "The verification email was not delivered. Please request a new code.",
                    409,
                )

            if otp_record.expires_at <= now:
                otp_record.invalidated_at = now
                db.commit()
                raise AuthError(
                    "The verification code has expired. Please request a new code.",
                    400,
                )

            if otp_record.attempts_count >= 5:
                otp_record.invalidated_at = now
                db.commit()
                raise AuthError(
                    "Too many incorrect attempts. Please request a new code.",
                    429,
                )

            if not verify_email_otp(request.otp, otp_record.otp_hash):
                otp_record.attempts_count += 1

                if otp_record.attempts_count >= 5:
                    otp_record.invalidated_at = now

                db.commit()

                if otp_record.attempts_count >= 5:
                    raise AuthError(
                        "Too many incorrect attempts. Please request a new code.",
                        429,
                    )

                raise AuthError(
                    "The verification code is incorrect.",
                    400,
                )

            # Activate only the initial registration Admin.
            otp_record.consumed_at = now
            user.account_status = AccountStatus.ACTIVE

            raw_refresh_token = generate_refresh_token()

            AuthService._create_refresh_session(
                db,
                user,
                raw_refresh_token,
                now,
            )

            db.commit()
            db.refresh(user)

            # Company status deliberately remains setup_pending.
            return AuthService._build_token_response(
                user,
                raw_refresh_token,
            )

        except AuthError:
            raise
        except Exception:
            db.rollback()
            raise

    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------

    @staticmethod
    def login(
        db: Session,
        request: LoginRequest,
    ) -> AuthTokenResponse:

        user = db.scalar(
            select(User).where(
                User.company_id == request.company_id,
                User.normalized_email == str(request.email).lower(),
            )
        )

        if user is None or not verify_password(
            request.password,
            user.password_hash,
        ):
            raise AuthError("Invalid email or password.", 401)

        if user.account_status != AccountStatus.ACTIVE:
            raise AuthError(
                "This account is not active. Complete email verification first.",
                403,
            )

        now = datetime.now(timezone.utc)
        raw_refresh_token = generate_refresh_token()

        try:
            AuthService._create_refresh_session(
                db,
                user,
                raw_refresh_token,
                now,
            )

            db.commit()

            return AuthService._build_token_response(
                user,
                raw_refresh_token,
            )

        except Exception:
            db.rollback()
            raise

    # --------------------------------------------------
    # REFRESH ACCESS TOKEN
    # --------------------------------------------------

    @staticmethod
    def refresh_access_token(
        db: Session,
        raw_refresh_token: str,
    ) -> AuthTokenResponse:

        now = datetime.now(timezone.utc)
        token_hash = hash_refresh_token(raw_refresh_token)

        try:
            session = db.scalar(
                select(RefreshSession)
                .where(RefreshSession.token_hash == token_hash)
                .with_for_update()
            )

            if session is None or session.revoked_at is not None:
                raise AuthError("Invalid refresh token.", 401)

            if session.expires_at <= now:
                session.revoked_at = now
                db.commit()
                raise AuthError("Refresh token has expired.", 401)

            user = db.scalar(
                select(User)
                .where(
                    User.company_id == session.company_id,
                    User.id == session.user_id,
                )
                .with_for_update()
            )

            if user is None or user.account_status != AccountStatus.ACTIVE:
                session.revoked_at = now
                db.commit()
                raise AuthError("This account is not active.", 403)

            # Revoke old token and create a new one.
            session.revoked_at = now
            new_refresh_token = generate_refresh_token()

            AuthService._create_refresh_session(
                db,
                user,
                new_refresh_token,
                now,
            )

            db.commit()

            return AuthService._build_token_response(
                user,
                new_refresh_token,
            )

        except AuthError:
            raise
        except Exception:
            db.rollback()
            raise

    # --------------------------------------------------
    # LOGOUT
    # --------------------------------------------------

    @staticmethod
    def logout(
        db: Session,
        raw_refresh_token: str,
    ) -> None:

        session = db.scalar(
            select(RefreshSession)
            .where(
                RefreshSession.token_hash
                == hash_refresh_token(raw_refresh_token)
            )
            .with_for_update()
        )

        if session is not None and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()

    # --------------------------------------------------
    # RESEND REGISTRATION OTP
    # --------------------------------------------------

    @staticmethod
    def resend_registration_otp(
        db: Session,
        request: ResendVerificationRequest,
    ) -> dict:

        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        try:
            user = db.scalar(
                select(User)
                .where(
                    User.company_id == request.company_id,
                    User.normalized_email == str(request.email).lower(),
                )
                .with_for_update()
            )

            if (
                user is None
                or user.role != UserRole.COMPANY_ADMIN
                or user.account_origin != AccountOrigin.REGISTRATION
                or user.account_status != AccountStatus.PENDING_ACTIVATION
            ):
                raise AuthError(
                    "Invalid or unavailable verification request.",
                    400,
                )

            # Maximum five OTP requests within one hour.
            recent_requests = db.scalar(
                select(func.count(EmailVerificationOTP.id)).where(
                    EmailVerificationOTP.company_id == user.company_id,
                    EmailVerificationOTP.user_id == user.id,
                    EmailVerificationOTP.created_at >= one_hour_ago,
                )
            ) or 0

            if recent_requests >= 5:
                raise AuthError(
                    "Maximum OTP requests reached. Try again later.",
                    429,
                )

            latest_otp = db.scalar(
                select(EmailVerificationOTP)
                .where(
                    EmailVerificationOTP.company_id == user.company_id,
                    EmailVerificationOTP.user_id == user.id,
                    EmailVerificationOTP.consumed_at.is_(None),
                    EmailVerificationOTP.invalidated_at.is_(None),
                )
                .order_by(EmailVerificationOTP.created_at.desc())
                .with_for_update()
            )

            # Enforce 60-second resend cooldown.
            if latest_otp is not None:
                if now - latest_otp.created_at < timedelta(seconds=60):
                    raise AuthError(
                        "Please wait 60 seconds before requesting another code.",
                        429,
                    )

                latest_otp.invalidated_at = now

            otp = generate_email_otp()

            new_otp = EmailVerificationOTP(
                company_id=user.company_id,
                user_id=user.id,
                otp_hash=hash_email_otp(otp),
                expires_at=now + timedelta(minutes=5),
                delivery_status=OTPDeliveryStatus.PENDING,
            )

            db.add(new_otp)
            db.commit()

        except AuthError:
            raise
        except Exception:
            db.rollback()
            raise

        # Email delivery happens after the database commit.
        try:
            send_admin_verification_otp_email(
                recipient_email=user.normalized_email,
                otp=otp,
            )

            new_otp.delivery_status = OTPDeliveryStatus.SENT
            new_otp.delivered_at = datetime.now(timezone.utc)

        except Exception:
            logger.exception("OTP resend email delivery failed.")

            new_otp.delivery_status = OTPDeliveryStatus.FAILED
            new_otp.delivered_at = None

        db.commit()

        return {
            "message": (
                "A new verification code has been sent."
                if new_otp.delivery_status == OTPDeliveryStatus.SENT
                else "The verification email could not be delivered. Please try again later."
            )
        }
