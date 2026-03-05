"""
config.py — Centralised application configuration.

All environment variables are loaded ONCE here via pydantic-settings.
Every other module imports Settings from this file.
No other file should call os.getenv() or read .env directly.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

# ---------------------------------------------------------------------------
# Resolve .env location
# config.py lives at: backend/app/config.py
# .env lives at:      <project_root>/.env  (one level above backend/)
# ---------------------------------------------------------------------------
_THIS_FILE = Path(__file__).resolve()           # backend/app/config.py
_BACKEND_DIR = _THIS_FILE.parent.parent         # backend/
_PROJECT_ROOT = _BACKEND_DIR.parent             # project root (Ai_Financial_Agent/)
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file at project root.
    pydantic-settings automatically reads the .env file and validates types.
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # Silently ignore unknown env vars
    )

    # ------------------------------------------------------------------
    # 🌐 Application
    # ------------------------------------------------------------------
    APP_NAME: str = Field(default="Financial Research Agent")
    APP_ENV: str = Field(default="development")           # development | production
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # ------------------------------------------------------------------
    # 🗄 Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(
        ...,
        description="SQLAlchemy-compatible DB URL. Use 'sqlite+aiosqlite:///...' for local, "
                    "'postgresql+asyncpg://...' for Render/production.",
    )

    # ------------------------------------------------------------------
    # 🧠 Vector Store (Qdrant)
    # ------------------------------------------------------------------
    QDRANT_URL: str = Field(default="", description="Qdrant cloud cluster URL")
    QDRANT_API_KEY: str = Field(default="", description="Qdrant API key")
    QDRANT_COLLECTION: str = Field(default="financial_insights")

    # ------------------------------------------------------------------
    # 🔐 Security
    # ------------------------------------------------------------------
    SECRET_KEY: str = Field(..., description="App secret key (JWT signing, etc.)")
    JWT_SECRET: str = Field(default="")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)

    # ------------------------------------------------------------------
    # 🤖 LLM Providers
    # ------------------------------------------------------------------
    LLM_PROVIDER: str = Field(default="groq")       # groq | gemini | disabled
    GROQ_API_KEY: str = Field(default="")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")

    # ------------------------------------------------------------------
    # 📊 Market Data
    # ------------------------------------------------------------------
    DATA_PROVIDERS: str = Field(default="yfinance")
    CACHE_ENABLED: bool = Field(default=True)
    CACHE_TTL_MINUTES: int = Field(default=60)

    # ------------------------------------------------------------------
    # 📈 Forecast / Analytics
    # ------------------------------------------------------------------
    FORECAST_HORIZON_DAYS: int = Field(default=30)
    MOVING_AVERAGE_SHORT: int = Field(default=20)
    MOVING_AVERAGE_LONG: int = Field(default=50)
    VOLATILITY_LOOKBACK_DAYS: int = Field(default=90)

    # ------------------------------------------------------------------
    # ⚠️ Risk / Scenario
    # ------------------------------------------------------------------
    DEFAULT_RECESSION_IMPACT: float = Field(default=-0.05)
    DEFAULT_INFLATION_IMPACT: float = Field(default=-0.03)
    DEFAULT_RATE_HIKE_IMPACT: float = Field(default=-0.02)

    # ------------------------------------------------------------------
    # 🧠 Agent settings
    # ------------------------------------------------------------------
    QUICK_MODE_TIMEOUT: int = Field(default=20)
    DEEP_MODE_TIMEOUT: int = Field(default=120)
    CONFIDENCE_THRESHOLD: float = Field(default=0.65)

    # ------------------------------------------------------------------
    # 👤 Personalisation defaults
    # ------------------------------------------------------------------
    DEFAULT_RISK_PROFILE: str = Field(default="moderate")
    DEFAULT_TIME_HORIZON: str = Field(default="long_term")

    # ------------------------------------------------------------------
    # ⚡ Performance / Demo  (Phase 16)
    # ------------------------------------------------------------------
    ENABLE_CACHE: bool = Field(default=True)
    CACHE_TTL: int = Field(default=300, description="L1 cache TTL in seconds")
    DEMO_MODE: bool = Field(default=False)
    DEMO_DEFAULT_TICKER: str = Field(default="AAPL")
    MAX_REQUESTS_PER_MINUTE: int = Field(default=20, description="Per-user rate limit")
    ENABLE_LLM: bool = Field(default=True, description="Master LLM toggle")

    # ------------------------------------------------------------------
    # 📊 Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = Field(default="INFO")
    ENABLE_PERFORMANCE_LOGS: bool = Field(default=True)

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("APP_ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        allowed = {"groq", "gemini", "local", "disabled"}
        if v.lower() not in allowed:
            raise ValueError(f"LLM_PROVIDER must be one of {allowed}, got '{v}'")
        return v.lower()


    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_debug(self) -> bool:
        return self.DEBUG

    @property
    def effective_log_level(self) -> str:
        """Return DEBUG in development, LOG_LEVEL otherwise."""
        if self.APP_ENV == "development" and self.DEBUG:
            return "DEBUG"
        return self.LOG_LEVEL


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.
    Use this everywhere: `from app.config import get_settings; settings = get_settings()`
    The lru_cache ensures .env is parsed only once per process.
    """
    return Settings()


# Module-level alias for convenience
settings = get_settings()
