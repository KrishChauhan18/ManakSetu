import os
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings and Security Configuration.
    Enforces 'secure-by-default' architecture:
    - Mandatory cryptographic SECRET_KEY from environment (min 32 chars).
    - Zero hardcoded database credentials.
    - Explicit, validated CORS allowed origins with no wildcard fallback.
    """
    PROJECT_NAME: str = "ComplyErg"
    API_V1_STR: str = "/api/v1"
    
    # Cryptographic JWT Settings (Must be set in environment or .env)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours default session
    
    # Database Settings (Environment-driven, zero hardcoded secrets)
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "complyerg_db"
    
    DATABASE_URL: Optional[str] = None
    SQLITE_FALLBACK_URL: str = "sqlite:///./storage/complyerg.db"
    
    # Storage Directories & Backend
    STORAGE_BACKEND: str = "local"
    STORAGE_DIR: str = os.path.join(os.getcwd(), "storage")
    
    # OCR Multi-Tier Cascade Settings
    GOOGLE_VISION_ENABLED: bool = False
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    PADDLEOCR_ENABLED: bool = True
    TESSERACT_ENABLED: bool = True
    TESSERACT_CMD: Optional[str] = None
    TESSERACT_LANG: str = "eng"
    TESSERACT_PSM: int = 11
    OCR_MIN_CONFIDENCE: float = 0.70
    OCR_ENGINE_AGREEMENT_THRESHOLD: float = 0.75
    
    # Rule Knowledge Base Seed Files
    RULES_SEED_FILE: str = os.path.join(os.getcwd(), "app", "rules_data", "legal_metrology_2011.json")
    DRUGS_RULES_SEED_FILE: str = os.path.join(os.getcwd(), "app", "rules_data", "drugs_cosmetics_1945.json")
    
    # CORS Origin Whitelist (Explicit, strictly no wildcard)
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, value: Optional[str]) -> str:
        """
        Enforce presence and cryptographic strength of SECRET_KEY.
        Fails application startup immediately if missing or inadequate.
        """
        val = value or os.getenv("SECRET_KEY")
        if not val or not isinstance(val, str) or len(val.strip()) < 32:
            raise RuntimeError(
                "FATAL SECURITY CONFIGURATION ERROR: 'SECRET_KEY' environment variable is missing, "
                "empty, or less than 32 characters in length. The application refuses to start with an insecure key. "
                "Please generate a secure secret using: python -c 'import secrets; print(secrets.token_urlsafe(32))' "
                "and define it in your .env file."
            )
        return val.strip()

    @property
    def cors_origins(self) -> List[str]:
        """
        Return a sanitized, deduplicated list of allowed CORS origins.
        Strictly strips out any wildcard '*' entries.
        """
        if isinstance(self.ALLOWED_ORIGINS, list):
            raw = [str(o).strip() for o in self.ALLOWED_ORIGINS if str(o).strip()]
        elif isinstance(self.ALLOWED_ORIGINS, str):
            raw = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        else:
            raw = []

        sanitized = [o for o in raw if o and o != "*"]
        if not sanitized:
            sanitized = ["http://localhost:5173", "http://127.0.0.1:5173"]
        return sanitized

    def model_post_init(self, __context) -> None:
        """
        Dynamically resolve DATABASE_URL if not explicitly set.
        Guarantees DATABASE_URL is never None for consumers.
        """
        super().model_post_init(__context)
        if not self.DATABASE_URL or not self.DATABASE_URL.strip():
            if self.POSTGRES_USER and self.POSTGRES_PASSWORD:
                self.DATABASE_URL = (
                    f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                    f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
                )
            else:
                self.DATABASE_URL = self.SQLITE_FALLBACK_URL


try:
    settings = Settings()
except Exception as exc:
    # Ensure immediate fatal halt on misconfiguration with clear diagnostic
    raise RuntimeError(f"Application configuration initialization failed: {exc}") from exc
