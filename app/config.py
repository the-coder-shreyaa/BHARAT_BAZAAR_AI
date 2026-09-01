"""
Application configuration loaded from environment variables.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env file and environment variables."""

    # Database
    DATABASE_URL: str = "sqlite:///bharat_bazaar.db"

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Razorpay (Test/Sandbox)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None

    # LLM Configuration (modular and configurable)
    LLM_PROVIDER: str = "none"  # "openai", "none" (rule-based fallback)
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = "https://api.openai.com/v1"

    # Merchant Info
    MERCHANT_NAME: str = "Bharat Bazaar"
    MERCHANT_DESCRIPTION: str = "India's premier AI-enabled fashion & lifestyle marketplace"
    MERCHANT_CURRENCY: str = "INR"

    @property
    def razorpay_enabled(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)

    @property
    def llm_enabled(self) -> bool:
        return self.LLM_PROVIDER != "none" and bool(self.LLM_API_KEY)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
