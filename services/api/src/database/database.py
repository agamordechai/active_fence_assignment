"""Database connection and session management"""
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import settings
from src.database.models import Base

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using them
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables"""
    logger.info(f"Initializing database at {settings.database_url}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def drop_db():
    """Drop all tables (use with caution!)"""
    logger.warning("Dropping all database tables")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped")


def reset_db():
    """Reset the database (drop and recreate all tables)"""
    logger.warning("Resetting database")
    drop_db()
    init_db()
    logger.info("Database reset complete")


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions

    Usage:
        with get_db_context() as db:
            db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
