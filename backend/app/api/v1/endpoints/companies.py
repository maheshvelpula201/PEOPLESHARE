
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_database_session
from app.schemas.company import (
    CompanyRegistrationRequest,
    CompanyRegistrationResponse,
)
from app.services.companies import (
    CompanyRegistrationConflict,
    CompanyService,
)


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.post(
    "/register",
    response_model=CompanyRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_company(
    registration: CompanyRegistrationRequest,
    db: Session = Depends(get_database_session),
) -> CompanyRegistrationResponse:
    try:
        return CompanyService.register_company(
            db=db,
            registration=registration,
        )

    except CompanyRegistrationConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
