"""
core/config.py — centralised settings for the v2 auth module.
Reads from environment / .env automatically via pydantic-settings.
All other modules import `settings` from here.
"""
from __future__ import annotations
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # silently ignore unrelated .env keys
    )

    # ── Database ─────────────────────────────────────────────
    # PostgreSQL in production  →  postgresql+psycopg2://user:pass@host/db
    # SQLite for local dev      →  sqlite:///./data/finx.db  (default)
    DATABASE_URL: str = "sqlite:///./data/finx.db"

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "dev-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # ── SMTP (Gmail App Password recommended) ────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""   # Brevo SMTP login (axxx@smtp-brevo.com)
    SMTP_PASS: str = ""   # Brevo SMTP key
    SMTP_FROM: str = ""   # Verified sender email shown in From header

    # ── URLs ─────────────────────────────────────────────────
    APP_URL: str = os.getenv("APP_URL", "http://localhost:5173")      # frontend
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")  # this server

    # ── Google OAuth ─────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # In local dev, the frontend runs on :5173 and proxies /api -> :8000.
    # Using a :5173 redirect keeps the auth session cookie on the same origin.
    GOOGLE_REDIRECT_URI: str = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "https://finx-1.onrender.com/api/v2/auth/google/callback"
)


settings = Settings()
