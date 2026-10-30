from sqlalchemy import func, select

from app.db.session import engine
from app.models.company import Company
from app.models.user import User

with engine.connect() as connection:
    company_count = connection.scalar(
        select(func.count()).select_from(Company)
    )

    user_count = connection.scalar(
        select(func.count()).select_from(User)
    )

    print(f"Existing companies: {company_count}")
    print(f"Existing users: {user_count}")