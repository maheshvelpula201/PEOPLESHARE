
from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailVerificationRequest(BaseModel):
    company_id: int = Field(gt=0)
    email: EmailStr
    otp: str = Field(pattern=r"^\d{6}$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    company_id: int = Field(gt=0)
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=255)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=255)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    user_id: int
    company_id: int
    email: EmailStr
    role: str
    
class ResendVerificationRequest(BaseModel):
    company_id: int = Field(gt=0)
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ResendVerificationResponse(BaseModel):
    message: str
