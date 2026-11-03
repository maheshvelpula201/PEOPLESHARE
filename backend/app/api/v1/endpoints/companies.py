
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
from app.schemas.auth import AuthTokenResponse, EmailVerificationRequest
from app.services.auth import AuthError, AuthService
from app.schemas.auth import ResendVerificationRequest


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
@router.post(
    "/verify-email",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
)
def verify_company_admin_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_database_session),
):
    try:
        return AuthService.verify_registration_email(db, request)
    except AuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc
@router.post("/resend-verification")
def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_database_session),
):
    try:
        return AuthService.resend_registration_otp(db, request)
    except AuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc
