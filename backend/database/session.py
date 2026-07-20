"""
Database connection setup.
Creates the SQLAlchemy engine (the thing that actually talks to Postgres)
and a session factory (used to open a "conversation" with the DB per request).
Every route that needs the DB will use `get_db()` below instead of connecting manually.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config.settings import settings

# The engine manages the actual connection pool to Postgres
engine = create_engine(settings.DATABASE_URL)

# SessionLocal is a factory that creates new DB sessions on demand
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class every table model will inherit from
Base = declarative_base()


def get_db():
    """
    FastAPI dependency: opens a DB session for a single request,
    and guarantees it's closed afterward, even if an error happens.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
