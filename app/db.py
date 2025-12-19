from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
import os

# Backward-compatible local engine/session for non-Flask contexts (e.g., scripts)
class Base(DeclarativeBase):
    pass

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/dragvest_cli")
engine = create_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)

def get_session() -> Session:
    """Return a SQLAlchemy session.

    In a Flask app context with Flask-SQLAlchemy registered, return db.session.
    Otherwise, fall back to a local SessionLocal bound to the engine above.
    """
    try:
        # Try to use Flask-SQLAlchemy session if available
        from flask import current_app
        if current_app:  # will raise RuntimeError if no app context
            from app.database import sqldb
            return sqldb.session  # type: ignore[return-value]
    except Exception:
        # no app context or extension not ready; fall back to local session
        pass
    return SessionLocal()
