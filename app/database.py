# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings  # Import the single source of truth

# 1. Get the URL directly from your Pydantic settings
#    (This automatically handles Docker env vars vs Local defaults)
DATABASE_URL = settings.DATABASE_URL

# 2. Ensure URL starts with postgresql:// 
#    (Fixes issue where some cloud providers like Heroku use 'postgres://')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

# 3. Create Engine
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

