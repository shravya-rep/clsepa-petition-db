from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CLSEPA Petition Decision Database"
    DATABASE_URL: str = "postgresql://localhost:5432/clsepa_petition_db"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"
    PDF_UPLOAD_DIR: str = "uploads/pdfs"

    class Config:
        env_file = ".env"


settings = Settings()
