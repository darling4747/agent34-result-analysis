"""Centralised configuration via pydantic-settings."""
from __future__ import annotations
import warnings
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    DATABASE_URL: str = 'postgresql+psycopg2://postgres:postgres@localhost:5432/result_analysis'
    FRONTEND_URL: str = 'http://localhost:5173'
    UPLOAD_DIR: str = 'uploads'
    REPORT_DIR: str = 'reports'
    INTERNAL_MAX: float = 30.0
    EXTERNAL_MAX: float = 70.0
    TOTAL_MAX: float = 100.0
    GRADE_MAP_JSON: str = '{"O":10,"A+":9,"A":8,"B+":7,"B":6,"C":5,"P":4,"F":0}'
    INTERVENTION_FAILURE_WEIGHT: float = 0.40
    INTERVENTION_HISTORICAL_WEIGHT: float = 0.30
    INTERVENTION_SECTION_WEIGHT: float = 0.20
    INTERVENTION_CORRELATION_WEIGHT: float = 0.10
    JWT_SECRET_KEY: str = 'Agent34_JWT_Dev_Secret_Please_Change_In_Production_32chars'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TEMP_PASSWORD_EXPIRY_HOURS: int = 24
    LLM_PROVIDER: str = 'gemini'
    LLM_API_KEY: str = ''
    LLM_MODEL: str = 'gemini-3.6-flash'

    @property
    def grade_map(self) -> dict[str, float]:
        return json.loads(self.GRADE_MAP_JSON)

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.DATABASE_URL.strip()
        if url.startswith("postgres://"):
            return "postgresql+psycopg2://" + url[len("postgres://"):]
        if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            return "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url

    @property
    def is_sqlite(self) -> bool:
        return self.sqlalchemy_database_url.startswith('sqlite')

    def warn_if_sqlite(self) -> None:
        if self.is_sqlite:
            warnings.warn(
                'SQLite is configured. This is only suitable for local development. '
                'Set DATABASE_URL to a PostgreSQL URL for production use.',
                stacklevel=2,
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()