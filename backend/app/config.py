# BaseSettings is a Pydantic class that reads values from environment variables and .env files
from pydantic_settings import BaseSettings


# Settings groups all runtime configuration into one validated, type-checked object
class Settings(BaseSettings):
    # Connection string for the database; defaults to a local SQLite file for development
    DATABASE_URL: str = "sqlite:///./lastkey.db"
    # Secret used to sign and verify JWT tokens — MUST be changed to a long random value in production
    SECRET_KEY: str = "change-this-in-production"
    # JWT signing algorithm — HS256 uses a shared symmetric secret
    ALGORITHM: str = "HS256"
    # Number of minutes before a JWT access token expires and the user must log in again
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Application environment name — used to enable/disable debug features (e.g., /docs in prod)
    APP_ENV: str = "development"
    # The URL where the React frontend is hosted — used for CORS whitelisting and email links
    FRONTEND_URL: str = "http://localhost:3000"
    # SMTP server hostname for outgoing email (check-in reminders, verifier alerts, etc.)
    SMTP_HOST: str = "smtp.gmail.com"
    # SMTP port — 587 is the standard STARTTLS submission port
    SMTP_PORT: int = 587
    # SMTP authentication username (usually the sending email address)
    SMTP_USER: str = ""
    # SMTP authentication password or app-specific password
    SMTP_PASSWORD: str = ""
    # The "From" address shown in all outgoing emails
    EMAIL_FROM: str = "noreply@lastkey.dev"
    # Number of days after the missed check-in deadline before the verifier is alerted
    GRACE_PERIOD_DAYS: int = 7
    # Number of days a one-click check-in token (sent via email) remains valid
    CHECKIN_TOKEN_EXPIRE_DAYS: int = 30
    # Number of days a beneficiary release link remains valid after secrets are released
    RELEASE_TOKEN_EXPIRE_DAYS: int = 90
    # Public base URL of this API server — used when constructing links in outgoing emails
    BASE_URL: str = "http://localhost:8000"

    # Pydantic inner Config class — instructs BaseSettings to load values from a .env file
    class Config:
        env_file = ".env"


# Instantiate a single settings object imported everywhere in the app
settings = Settings()
