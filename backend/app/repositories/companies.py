
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company, CompanyStatus


class CompanyRepository:

    @staticmethod
    def create(
        db: Session,
        *,
        name: str,
        slug: str,
        timezone_name: str,
    ) -> Company:
        company = Company(
            name=name,
            slug=slug,
            timezone_name=timezone_name,
            status=CompanyStatus.SETUP_PENDING,
        )

        db.add(company)
        db.flush()

        return company

    @staticmethod
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Company | None:
        statement = select(Company).where(
            Company.slug == slug
        )

        return db.scalar(statement)

    @staticmethod
    def slug_exists(
        db: Session,
        slug: str,
    ) -> bool:
        statement = select(Company.id).where(
            Company.slug == slug
        )

        return db.scalar(statement) is not None
