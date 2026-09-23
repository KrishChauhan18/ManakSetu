from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    JWT_SECRET: str
    JWT_EXPIRE_HOURS: int = 8

    # PostgreSQL connection
    DATABASE_URL: str = "postgresql://postgres:9876@localhost:5432/manak_setu"

    # ComplyErg compliance engine (runs on port 8001)
    COMPLYERG_ENGINE_URL: str = "http://127.0.0.1:8001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()