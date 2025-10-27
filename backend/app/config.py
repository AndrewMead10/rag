from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    # JWT Configuration
    jwt_secret: str = Field(..., env="JWT_SECRET")
    access_token_ttl_minutes: int = Field(15, env="ACCESS_TOKEN_TTL_MINUTES")
    refresh_token_ttl_days: int = Field(30, env="REFRESH_TOKEN_TTL_DAYS")
    
    # Database
    database_url: str = Field("sqlite:///./data/service.db", env="DATABASE_URL")

    # CORS
    cors_origins: list[str] = Field(["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    
    # Feature Flags
    enable_user_registration: bool = Field(True, env="ENABLE_USER_REGISTRATION")
    enable_password_reset: bool = Field(True, env="ENABLE_PASSWORD_RESET")
    enable_admin_panel: bool = Field(True, env="ENABLE_ADMIN_PANEL")
    enable_backups: bool = Field(True, env="ENABLE_BACKUPS")
    
    # R2 Backup (optional)
    enable_r2_backup: bool = Field(False, env="ENABLE_R2_BACKUP")
    r2_account_id: str = Field("", env="R2_ACCOUNT_ID")
    r2_access_key_id: str = Field("", env="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field("", env="R2_SECRET_ACCESS_KEY")
    r2_bucket: str = Field("", env="R2_BUCKET")
    
    # Email (SES)
    ses_from_email: str = Field("", env="SES_FROM_EMAIL")
    aws_access_key_id: str = Field("", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field("", env="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field("us-east-1", env="AWS_DEFAULT_REGION")
    frontend_url: str = Field("http://localhost:3000", env="FRONTEND_URL")

    # Cookies
    cookie_secure: bool = Field(False, env="COOKIE_SECURE")
    
    # Google OAuth
    google_client_id: str = Field("", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        "http://localhost:8000/auth/google/callback", env="GOOGLE_REDIRECT_URI"
    )
    google_allowed_domains: list[str] = Field(
        default_factory=list, env="GOOGLE_ALLOWED_DOMAINS"
    )

    # Always use .env in project root
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
