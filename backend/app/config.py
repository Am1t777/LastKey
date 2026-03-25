from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./lastkey.db"
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@lastkey.dev"
    GRACE_PERIOD_DAYS: int = 7
    CHECKIN_TOKEN_EXPIRE_DAYS: int = 30
    RELEASE_TOKEN_EXPIRE_DAYS: int = 90
    BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
