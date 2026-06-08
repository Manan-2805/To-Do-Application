from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application Settings
    APP_NAME: str = "TodoSphere API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Security & Authentication
    # In production, these must be overridden with strong random keys
    JWT_ACCESS_SECRET: str = "super_secret_access_key_todosphere_1234567890"
    JWT_REFRESH_SECRET: str = "super_secret_refresh_key_todosphere_0987654321"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database & Cache
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/todosphere"
    REDIS_URL: str = "redis://redis:6379/0"

    # CORS Configuration
    # Safe fallback for development
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Storage Settings
    STORAGE_PROVIDER: str = "local"  # "local" or "s3"
    UPLOAD_DIR: str = "/app/uploads"
    S3_BUCKET_NAME: str = "todosphere-attachments"
    S3_ACCESS_KEY: str = "minio_dev_access_key"
    S3_SECRET_KEY: str = "minio_dev_secret_key"
    S3_ENDPOINT_URL: str = "http://minio:9000"


settings = Settings()
