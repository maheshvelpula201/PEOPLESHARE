
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_database_session
from app.schemas.auth import (
    AuthTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
)
from app.services.auth import AuthError, AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=AuthTokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_database_session),
):
    try:
        return AuthService.login(db, request)
    except AuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


@router.post("/refresh", response_model=AuthTokenResponse)
def refresh(
    request: RefreshRequest,
    db: Session = Depends(get_database_session),
):
    try:
        return AuthService.refresh_access_token(
            db,
            request.refresh_token,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_database_session),
):
    AuthService.logout(db, request.refresh_token)
    return {"message": "Logged out successfully."}
