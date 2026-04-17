"""
Single Source of Truth para configuración de la aplicación.

Lee variables de entorno desde .env y las valida con Pydantic V2.
Si falta una variable crítica, la app NO arranca (fail-fast).
"""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignora vars extra del .env sin romper
    )

    # --- Database ---
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")

    # --- Redis ---
    REDIS_URL: str = Field(..., description="Redis connection URL with auth")
    REDIS_POOL_MAX_CONNECTIONS: int = Field(
        default=20,
        description="Max connections in the Redis pool",
    )

    # --- Security (solo lectura, no lo usamos aún) ---
    JWT_SECRET_KEY: str = Field(..., description="JWT signing key")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # --- AI ---
    GOOGLE_API_KEY: str | None = Field(default=None)

    # --- Environment ---
    ENVIRONMENT: str = Field(default="development")


@lru_cache
def get_settings() -> Settings:
    """
    Cacheada para no releer el .env en cada request.
    Inyectable como dependency de FastAPI.
    """
    return Settings()