from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection settings
DB_USER = os.getenv("POSTGRES_USER", "dev")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "dev")
DB_NAME = os.getenv("POSTGRES_DB", "crisis")
DB_HOST = os.getenv("DB_HOST", "db")  # 'db' for Docker, 'localhost' for local
DB_PORT = os.getenv("DB_PORT", "5432")

# Construct the database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# For SQLAlchemy 2.0
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting async DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database by creating all tables.
    Should be called during application startup.
    """
    Base.metadata.create_all(bind=engine)
