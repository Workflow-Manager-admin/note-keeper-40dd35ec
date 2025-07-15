import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL (sqlite for demo, can be replaced with .env variable)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
