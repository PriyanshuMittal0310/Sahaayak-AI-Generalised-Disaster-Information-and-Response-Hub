from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Use localhost:5433 for local development (Docker db), db:5432 for Docker containers
if os.getenv("DOCKER_ENV"):
    # Running inside Docker container
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dev:dev@db:5432/crisis")
else:
    # Running locally, connecting to Docker database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dev:dev@localhost:5433/crisis")

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
