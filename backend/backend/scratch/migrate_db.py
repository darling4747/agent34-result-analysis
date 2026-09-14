"""Migration script to ensure all MFA columns and tables exist in PostgreSQL / SQLite."""
from sqlalchemy import text
from app.database import engine, Base
import app.models  # noqa: F401

print("Creating missing tables...")
Base.metadata.create_all(bind=engine)

print("Adding missing MFA columns to users table if not exists...")
with engine.connect() as conn:
    cols_to_add = [
        ("mfa_enabled", "BOOLEAN DEFAULT FALSE NOT NULL"),
        ("mfa_secret_encrypted", "VARCHAR(512)"),
        ("mfa_pending_secret_encrypted", "VARCHAR(512)"),
        ("mfa_verified_at", "TIMESTAMP"),
        ("mfa_enabled_at", "TIMESTAMP"),
    ]
    for col_name, col_def in cols_to_add:
        try:
            if "sqlite" in str(engine.url):
                # SQLite syntax
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
            else:
                # PostgreSQL syntax
                conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def}"))
            conn.commit()
            print(f"Added column {col_name}")
        except Exception as e:
            print(f"Column {col_name} check: {e}")

print("Migration complete!")
