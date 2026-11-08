"""Kết nối SQL Server bằng SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

engine = (
    create_engine(settings.database_url, pool_pre_ping=True)
    if settings.database_url
    else None
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None


def get_db() -> Generator[Session, None, None]:
    """Cấp một phiên DB cho request và đóng phiên sau khi hoàn tất."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL chưa được cấu hình trong file .env")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
