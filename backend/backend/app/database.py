"""SQLAlchemy engine, session factory, and Base - SQLite (dev) / PostgreSQL (prod)."""
from __future__ import annotations
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from .config import get_settings


class Base(DeclarativeBase):
    pass


def _get_engine():
    settings = get_settings()
    url = settings.sqlalchemy_database_url
    if url.startswith("sqlite"):
        eng = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(eng, "connect")
        def _pragmas(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
        return eng
    # PostgreSQL with connection pooling
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (idempotent) and auto-migrate missing user columns."""
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Lightweight migration for pre-existing 'users' table
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("users")}
        is_postgres = engine.dialect.name == "postgresql"
        mfa_cols = [
            ("mfa_enabled", "BOOLEAN DEFAULT FALSE NOT NULL"),
            ("mfa_secret_encrypted", "VARCHAR(255) NULL"),
            ("mfa_pending_secret_encrypted", "VARCHAR(255) NULL"),
            ("mfa_verified_at", "TIMESTAMP WITH TIME ZONE NULL" if is_postgres else "DATETIME NULL"),
            ("mfa_enabled_at", "TIMESTAMP WITH TIME ZONE NULL" if is_postgres else "DATETIME NULL"),
        ]
        with engine.begin() as conn:
            for col_name, col_def in mfa_cols:
                if col_name not in existing_cols:
                    if is_postgres:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def};"))
                    else:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};"))

