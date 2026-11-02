
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    generate_admin_activation_token,
    hash_admin_activation_token,
)
from app.models.admin_activation_token import (
    AdminActivationToken,
    ActivationDeliveryStatus,
    ActivationTokenStatus,
)
from app.models.audit_event import AuditEvent
from app.models.user import (
    AccountOrigin,
    AccountStatus,
    User,
    UserRole,
)
from app.services.email import send_admin_activation_email


class AdminActivationError(Exception):
    """Base exception for Admin activation errors."""


class AdminActivationNotAllowed(AdminActivationError):
    pass


class AdminActivationRateLimited(AdminActivationError):
    pass


class AdminActivationInvalidToken(AdminActivationError):
    pass


class AdminActivationDeliveryError(AdminActivationError):
    pass


class AdminActivationService:

    TOKEN_LIFETIME = timedelta(hours=24)
    RESEND_COOLDOWN = timedelta(seconds=60)
    MAX_REQUESTS_PER_HOUR = 5

    @staticmethod
    def _is_eligible_user(user: User | None) -> bool:
        return (
            user is not None
            and user.role == UserRole.COMPANY_ADMIN
            and user.account_origin == AccountOrigin.REGISTRATION
            and user.account_status == AccountStatus.PENDING_ACTIVATION
        )

    @staticmethod
    def issue_or_resend(
        db: Session,
        *,
        user_id: int,
    ) -> None:
        now = datetime.now(timezone.utc)

        try:
            # Lock the user first to serialize requests for this account.
            user = db.scalar(
                select(User)
                .where(User.id == user_id)
                .with_for_update()
            )

            if not AdminActivationService._is_eligible_user(user):
                raise AdminActivationNotAllowed(
                    "This account cannot receive an activation link."
                )

            requests_last_hour = db.scalar(
                select(func.count(AdminActivationToken.id)).where(
                    AdminActivationToken.company_id == user.company_id,
                    AdminActivationToken.user_id == user.id,
                    AdminActivationToken.created_at
                    >= now - timedelta(hours=1),
                )
            )

            if (
                requests_last_hour
                >= AdminActivationService.MAX_REQUESTS_PER_HOUR
            ):
                raise AdminActivationRateLimited(
                    "Too many activation requests. Please try again later."
                )

            latest_token = db.scalar(
                select(AdminActivationToken)
                .where(
                    AdminActivationToken.company_id == user.company_id,
                    AdminActivationToken.user_id == user.id,
                )
                .order_by(AdminActivationToken.created_at.desc())
                .limit(1)
            )

            if (
                latest_token is not None
                and latest_token.created_at
                > now - AdminActivationService.RESEND_COOLDOWN
            ):
                raise AdminActivationRateLimited(
                    "Please wait before requesting another activation link."
                )

            # Revoke all previous pending tokens.
            pending_tokens = db.scalars(
                select(AdminActivationToken)
                .where(
                    AdminActivationToken.company_id == user.company_id,
                    AdminActivationToken.user_id == user.id,
                    AdminActivationToken.status
                    == ActivationTokenStatus.PENDING,
                )
                .with_for_update()
            ).all()

            for old_token in pending_tokens:
                old_token.status = ActivationTokenStatus.REVOKED

            raw_token = generate_admin_activation_token()

            activation_token = AdminActivationToken(
                company_id=user.company_id,
                user_id=user.id,
                token_hash=hash_admin_activation_token(raw_token),
                status=ActivationTokenStatus.PENDING,
                delivery_status=ActivationDeliveryStatus.PENDING,
                expires_at=now + AdminActivationService.TOKEN_LIFETIME,
            )

            db.add(activation_token)
            db.flush()

            company_id = user.company_id
            recipient_email = user.normalized_email
            token_id = activation_token.id

            # Persist the token before attempting email delivery.
            db.commit()

        except Exception:
            db.rollback()
            raise

        activation_url = (
            f"{settings.admin_activation_base_url}?"
            f"{urlencode({'token': raw_token})}"
        )

        # Send the email only after the token has been committed.
        try:
            send_admin_activation_email(
                recipient_email=recipient_email,
                activation_url=activation_url,
            )

        except Exception as exc:
            db.rollback()

            try:
                current_user = db.scalar(
                    select(User)
                    .where(User.id == user_id)
                    .with_for_update()
                )

                failed_token = db.scalar(
                    select(AdminActivationToken)
                    .where(
                        AdminActivationToken.id == token_id,
                        AdminActivationToken.company_id == company_id,
                        AdminActivationToken.user_id == user_id,
                    )
                    .with_for_update()
                )

                if (
                    AdminActivationService._is_eligible_user(current_user)
                    and failed_token is not None
                    and failed_token.status == ActivationTokenStatus.PENDING
                ):
                    failed_token.delivery_status = (
                        ActivationDeliveryStatus.FAILED
                    )
                    db.commit()
                else:
                    db.rollback()

            except Exception:
                db.rollback()

            raise AdminActivationDeliveryError(
                "Activation email could not be delivered."
            ) from exc

        # Mark the token as delivered only if it is still valid
        # and has not been revoked by a newer resend request.
        try:
            db.rollback()

            current_user = db.scalar(
                select(User)
                .where(User.id == user_id)
                .with_for_update()
            )

            delivered_token = db.scalar(
                select(AdminActivationToken)
                .where(
                    AdminActivationToken.id == token_id,
                    AdminActivationToken.company_id == company_id,
                    AdminActivationToken.user_id == user_id,
                )
                .with_for_update()
            )

            if (
                delivered_token is not None
                and delivered_token.status == ActivationTokenStatus.PENDING
                and AdminActivationService._is_eligible_user(current_user)
            ):
                delivered_token.delivery_status = (
                    ActivationDeliveryStatus.SENT
                )
                delivered_token.delivered_at = datetime.now(timezone.utc)
                db.commit()

            else:
                # The account became ineligible or a newer request
                # already revoked this token.
                if (
                    delivered_token is not None
                    and delivered_token.status == ActivationTokenStatus.PENDING
                ):
                    delivered_token.status = ActivationTokenStatus.REVOKED

                db.commit()

        except Exception as exc:
            db.rollback()
            raise AdminActivationError(
                "Email delivery status could not be recorded."
            ) from exc

    @staticmethod
    def activate(
        db: Session,
        *,
        raw_token: str,
    ) -> None:
        token_hash = hash_admin_activation_token(raw_token)

        # This lookup only discovers the associated user.
        candidate = db.scalar(
            select(AdminActivationToken).where(
                AdminActivationToken.token_hash == token_hash
            )
        )

        if candidate is None:
            raise AdminActivationInvalidToken(
                "Invalid or expired activation link."
            )

        try:
            # Always lock the user before locking the token.
            user = db.scalar(
                select(User)
                .where(
                    User.id == candidate.user_id,
                    User.company_id == candidate.company_id,
                )
                .with_for_update()
            )

            activation_token = db.scalar(
                select(AdminActivationToken)
                .where(
                    AdminActivationToken.id == candidate.id,
                    AdminActivationToken.company_id == candidate.company_id,
                    AdminActivationToken.user_id == candidate.user_id,
                )
                .with_for_update()
            )

            now = datetime.now(timezone.utc)

            if (
                not AdminActivationService._is_eligible_user(user)
                or activation_token is None
                or activation_token.token_hash != token_hash
                or activation_token.status != ActivationTokenStatus.PENDING
                or activation_token.delivery_status
                != ActivationDeliveryStatus.SENT
                or activation_token.expires_at <= now
            ):
                raise AdminActivationInvalidToken(
                    "Invalid or expired activation link."
                )

            # Activate the account and consume the token atomically.
            user.account_status = AccountStatus.ACTIVE

            activation_token.status = ActivationTokenStatus.CONSUMED
            activation_token.consumed_at = now

            db.add(
                AuditEvent(
                    company_id=user.company_id,
                    actor_user_id=user.id,
                    action="admin_account_activated",
                    target_type="user",
                    target_id=str(user.id),
                    outcome="success",
                    event_data={},
                )
            )

            db.commit()

        except Exception:
            db.rollback()
            raise
