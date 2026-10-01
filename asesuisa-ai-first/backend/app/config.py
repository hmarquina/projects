"""Configuración por entorno. Los secretos nunca se hardcodean."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/dev.db"
    jwt_secret: str = Field(default="", repr=False)
    jwt_issuer: str = "ai-control-tower"
    jwt_ttl_minutes: int = 60
    demo_password: str = Field(default="", repr=False)
    ai_provider: str = "mock"

    def require_jwt_secret(self) -> str:
        if len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET debe definirse por entorno (mínimo 32 caracteres)")
        return self.jwt_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
