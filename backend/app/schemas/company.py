
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

class CompanyRegistrationRequest(BaseModel):
    company_name: str = Field(
        min_length=2,
        max_length=150,
    )

    admin_email: EmailStr

    password: str = Field(
        min_length=12,
        max_length=128,
    )

    timezone_name: str = Field(
        default="UTC",
        min_length=1,
        max_length=100,
    )

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Company name cannot be empty.")

        return value

    @field_validator("admin_email")
    @classmethod
    def normalize_admin_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("timezone_name")
    @classmethod
    def validate_timezone_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Timezone cannot be empty.")

        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Invalid timezone name.")

        return value


class CompanyRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    company_name: str
    company_slug: str
    company_status: str

    admin_user_id: int
    admin_email: str
    admin_role: str
    admin_account_status: str
