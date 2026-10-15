import os
from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project Metadata
    PROJECT_NAME: str = "Kestral Forensic Evidence Platform"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/kestral_db",
        description="SQLAlchemy connection URI (PostgreSQL or SQLite)"
    )
    TEST_DATABASE_URL: str = "sqlite:///./test_kestral.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            return v
        v = v.strip()
        # Normalization for hosted PostgreSQL providers (Supabase, Render, Railway, Heroku)
        if v.startswith("postgres://"):
            v = "postgresql+psycopg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
            v = "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def validate_production_database_url(cls, v: str, info: ValidationInfo) -> str:
        env = info.data.get("ENVIRONMENT", "development")
        if env and str(env).lower() == "production":
            # In production, prevent silent fallback to unreachable localhost:5432
            if "@localhost" in v or "@127.0.0.1" in v:
                raise ValueError(
                    "DATABASE_URL points to localhost/127.0.0.1 while ENVIRONMENT=production. "
                    "A valid production PostgreSQL connection string (such as Supabase or managed PostgreSQL) must be provided."
                )
        return v


    # Security & JWT
    JWT_SECRET_KEY: str = Field(
        default="kestral-super-secret-jwt-key-2026-production-ready-32bytes",
        description="Cryptographic secret key for signing JWT tokens"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STORAGE_ROOT: str = "."
    MAX_UPLOAD_SIZE_BYTES: int = 500 * 1024 * 1024  # 500 MB

    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_UPLOADS_PER_MINUTE: int = 30
    RATE_LIMIT_EXPORTS_PER_MINUTE: int = 20

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "*"

    # First Bootstrap Administrator
    FIRST_SUPERUSER_EMAIL: str = "admin@kestral.ai"
    FIRST_SUPERUSER_PASSWORD: str = "Admin123!SecurePassword"
    FIRST_SUPERUSER_NAME: str = "System Administrator"

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def uploads_path(self) -> str:
        path = os.path.join(self.BASE_DIR, "uploads")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def results_path(self) -> str:
        path = os.path.join(self.BASE_DIR, "results")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def faces_path(self) -> str:
        path = os.path.join(self.BASE_DIR, "faces")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def frames_path(self) -> str:
        path = os.path.join(self.BASE_DIR, "frames")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def exports_path(self) -> str:
        path = os.path.join(self.BASE_DIR, "exports")
        os.makedirs(path, exist_ok=True)
        return path

    # Compatibility properties for services
    @property
    def FACES_DIR(self) -> str:
        return self.faces_path

    @property
    def FRAMES_DIR(self) -> str:
        return self.frames_path

    @property
    def EXPORTS_DIR(self) -> str:
        return self.exports_path

    @property
    def UPLOADS_DIR(self) -> str:
        return self.uploads_path

    @property
    def RESULTS_DIR(self) -> str:
        return self.results_path

    @property
    def BASE_STORAGE_DIR(self) -> str:
        return self.BASE_DIR

    def init_storage_dirs(self):
        for p in [self.uploads_path, self.results_path, self.faces_path, self.frames_path, self.exports_path]:
            os.makedirs(p, exist_ok=True)

    def get_storage_path(self, rel_path: str) -> str:
        clean = rel_path.lstrip("/\\")
        return os.path.join(self.BASE_DIR, clean)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
