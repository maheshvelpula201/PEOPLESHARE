
import re
import unicodedata

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import AccountStatus, UserRole
from app.repositories.companies import CompanyRepository
from app.repositories.users import UserRepository
from app.schemas.company import (
    CompanyRegistrationRequest,
    CompanyRegistrationResponse,
)


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

        # Hash the password only once, even if slug retries are needed.
        password_hash = hash_password(registration.password)

        for attempt in range(CompanyService.MAX_SLUG_ATTEMPTS):

            company_slug = CompanyService.generate_unique_slug(
                db,
                registration.company_name,
            )

            try:
                # Create the company.
                company = CompanyRepository.create(
                    db,
                    name=registration.company_name,
                    slug=company_slug,
                    timezone_name=registration.timezone_name,
                )

                # Create its initial Company Admin.
                admin = UserRepository.create(
                    db,
                    company_id=company.id,
                    normalized_email=str(registration.admin_email),
                    password_hash=password_hash,
                    role=UserRole.COMPANY_ADMIN,
                    account_status=AccountStatus.PENDING_ACTIVATION,
                )

                # Commit both records in one transaction.
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
