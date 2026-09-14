"""FastAPI dependency injection helpers."""
from .database import get_db
from .config import get_settings, Settings
from sqlalchemy.orm import Session
from fastapi import Depends


def db_dependency(db: Session = Depends(get_db)) -> Session:
    return db


def settings_dependency(settings: Settings = Depends(get_settings)) -> Settings:
    return settings
