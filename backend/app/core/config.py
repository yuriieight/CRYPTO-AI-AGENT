from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Server
    SECRET_KEY: str
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database
    DATABASE_URL: str = "postgresql://crypto_user:crypto_password@localhost:5432/crypto_ai_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # API Keys
    ANTHROPIC_API_KEY: str
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    ALPHA_VANTAGE_KEY: str
    CRYPTOCOMPARE_API_KEY: str
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str = ""  # Optional
    GROQ_API_KEY: str = ""  # <--- ДОДАНО КЛЮЧ ДЛЯ GROQ

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # <--- ДОДАНО: ігнорувати будь-які інші невідомі ключі в .env

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]


settings = Settings()