import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use SQLITE for local dev by default. For deployment, set DATABASE_URL env var.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./upi.db")

# For sqlite only: connect args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
