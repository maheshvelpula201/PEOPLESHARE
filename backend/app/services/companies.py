import logging
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import generate_email_otp, hash_email_otp, hash_password
from app.models.email_verification_otp import (
    EmailVerificationOTP,
    OTPDeliveryStatus,
)
from app.models.user import AccountOrigin, AccountStatus, UserRole
from app.repositories.companies import CompanyRepository
from app.repositories.users import UserRepository
from app.schemas.company import (
    CompanyRegistrationRequest,
    CompanyRegistrationResponse,
)
from app.services.email import send_admin_verification_otp_email


logger = logging.getLogger(__name__)


class CompanyRegistrationConflict(Exception):
    """Raised when company registration conflicts with existing data."""


class CompanyService:

    MAX_SLUG_ATTEMPTS = 5

    @staticmethod
    def generate_base_slug(company_name: str) -> str:
        normalized = unicodedata.normalize("NFKD", company_name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name)
        slug = slug.strip("-").lower()
        slug = slug[:100].strip("-")

        return slug or "company"

    @staticmethod
    def generate_unique_slug(
        db: Session,
        company_name: str,
    ) -> str:
        base_slug = CompanyService.generate_base_slug(company_name)

        slug = base_slug
        counter = 2

        while CompanyRepository.slug_exists(db, slug):
            suffix = f"-{counter}"
            slug = f"{base_slug[:100 - len(suffix)]}{suffix}"
            counter += 1

        return slug

    @staticmethod
    def register_company(
        db: Session,
        registration: CompanyRegistrationRequest,
    ) -> CompanyRegistrationResponse:

        password_hash = hash_password(registration.password)

        for attempt in range(CompanyService.MAX_SLUG_ATTEMPTS):

            company_slug = CompanyService.generate_unique_slug(
                db,
                registration.company_name,
            )

            try:
                company = CompanyRepository.create(
                    db,
                    name=registration.company_name,
                    slug=company_slug,
                    timezone_name=registration.timezone_name,
                )

                admin = UserRepository.create(
                    db,
                    company_id=company.id,
                    normalized_email=str(registration.admin_email),
                    password_hash=password_hash,
                    role=UserRole.COMPANY_ADMIN,
                    account_status=AccountStatus.PENDING_ACTIVATION,
                    account_origin=AccountOrigin.REGISTRATION,
                )

                # Generate a secure six-digit OTP.
                otp = generate_email_otp()

                # Store only its HMAC hash in the database.
                otp_record = EmailVerificationOTP(
                    company_id=company.id,
                    user_id=admin.id,
                    otp_hash=hash_email_otp(otp),
                    expires_at=datetime.now(timezone.utc)
                    + timedelta(minutes=5),
                    delivery_status=OTPDeliveryStatus.PENDING,
                )

                db.add(otp_record)

                # Save company, admin and OTP together.
                db.commit()

                # Send email only after the database transaction succeeds.
                try:
                    send_admin_verification_otp_email(
                        recipient_email=admin.normalized_email,
                        otp=otp,
                    )

                    otp_record.delivery_status = OTPDeliveryStatus.SENT
                    otp_record.delivered_at = datetime.now(timezone.utc)

                except Exception:
                    logger.exception(
                        "Failed to send registration OTP to %s",
                        admin.normalized_email,
                    )

                    otp_record.delivery_status = OTPDeliveryStatus.FAILED
                    otp_record.delivered_at = None

                # Save the email delivery result.
                db.commit()

                return CompanyRegistrationResponse(
                    company_id=company.id,
                    company_name=company.name,
                    company_slug=company.slug,
                    company_status=company.status.value,
                    admin_user_id=admin.id,
                    admin_email=admin.normalized_email,
                    admin_role=admin.role.value,
                    admin_account_status=admin.account_status.value,
                )

            except IntegrityError as exc:
                db.rollback()

                original_error = exc.orig
                error_details = getattr(original_error, "diag", None)
                violated_constraint = getattr(
                    error_details,
                    "constraint_name",
                    None,
                )

                if violated_constraint == "ix_companies_slug":
                    continue

                raise CompanyRegistrationConflict(
                    "Company registration conflicts with existing data."
                ) from exc

            except Exception:
                db.rollback()
                raise

        raise CompanyRegistrationConflict(
            "Unable to generate a unique company slug. Please try again."
        )