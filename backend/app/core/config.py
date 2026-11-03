
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PeopleSphere"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: SecretStr

    # Email OTP security
    email_otp_hmac_secret: SecretStr = SecretStr("")

    # Authentication and JWT
    jwt_secret: SecretStr
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # SMTP configuration
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_sender_email: str = ""
    smtp_sender_name: str = "PeopleSphere"
    smtp_use_tls: bool = True

    # Legacy activation setting; retained temporarily during migration.
    admin_activation_base_url: str = "http://localhost:3000/activate-admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
