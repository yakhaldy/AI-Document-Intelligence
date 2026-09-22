"""Shared FastAPI dependencies: DB session, current tenant."""
import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import default_tenant_id

load_dotenv()

_engine = None
_SessionLocal = None


def _get_session_factory():
    global _engine, _SessionLocal
    if _SessionLocal is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL manquant (voir .env)")
        _engine = create_engine(url)
        _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = _get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def get_tenant_id():
    return default_tenant_id()
