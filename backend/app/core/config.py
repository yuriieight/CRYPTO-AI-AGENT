"""Pydantic Settings – load from .env file."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/crypto_db"
    REDIS_URL: str    = "redis://localhost:6379"
    SECRET_KEY: str   = "change-me"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str    = ""
    GOOGLE_API_KEY: str    = ""
    GROQ_API_KEY: str      = ""
    CRYPTOCOMPARE_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
