import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger("manak_setu.db")

DATABASE_URL = settings.DATABASE_URL

def create_resilient_engine():
    # If DATABASE_URL is SQLite, create directly
    if DATABASE_URL.startswith("sqlite"):
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Try connecting to PostgreSQL
    try:
        pg_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[DB] Successfully connected to PostgreSQL database.")
        return pg_engine
    except Exception as exc:
        logger.warning(
            f"[DB] PostgreSQL connection failed ({exc}). "
            "Falling back to local SQLite: sqlite:///./manak_setu.db"
        )
        sqlite_engine = create_engine(
            "sqlite:///./manak_setu.db",
            connect_args={"check_same_thread": False}
        )
        return sqlite_engine

engine = create_resilient_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()