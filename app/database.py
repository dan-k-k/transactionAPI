# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Force a default Postgres URL (for local dev) if env var is missing
#    Format: postgresql://user:password@host:port/db_name
DEFAULT_DB_URL = "postgresql://user:password@localhost:5432/transactions_db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# 2. Ensure URL starts with postgresql:// (Fix for some cloud providers/older URLs)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

# 3. Create Engine - clean and simple
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

