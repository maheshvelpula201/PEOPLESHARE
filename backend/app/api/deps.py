
from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db


def get_database_session() -> Generator[Session, None, None]:
    """
    Provide a database session to API endpoints.

    The session is automatically closed after the request.
    """
    yield from get_db()
