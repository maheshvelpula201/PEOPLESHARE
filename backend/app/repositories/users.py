
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import (
    AccountStatus,
    User,
    UserRole,
)


class UserRepository:

    @staticmethod
    def create(
        db: Session,
        *,
        company_id: int,
        normalized_email: str,
        password_hash: str,
        role: UserRole,
        account_status: AccountStatus = AccountStatus.PENDING_ACTIVATION,
    ) -> User:
        user = User(
            company_id=company_id,
            normalized_email=normalized_email,
            password_hash=password_hash,
            role=role,
            account_status=account_status,
        )

        db.add(user)
        db.flush()

        return user

    @staticmethod
    def get_by_company_email(
        db: Session,
        *,
        company_id: int,
        normalized_email: str,
    ) -> User | None:
        statement = select(User).where(
            User.company_id == company_id,
            User.normalized_email == normalized_email,
        )

        return db.scalar(statement)
