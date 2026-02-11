# tests/conftest.py
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Import your app and global variables
from app.main import app, get_engine, get_db
from app.database import Base

# 1. Determine DB URL
# Use a specific test database name to avoid wiping dev data
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://user:password@localhost:5432/test_transactions_db" 
)

# Fix for some environments providing 'postgres://'
if TEST_DATABASE_URL.startswith("postgres://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgres://", "postgresql://")

# 2. Configure Engine
test_engine = create_engine(TEST_DATABASE_URL)

# 3. Create Testing Session
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    pass

@pytest.fixture(scope="function")
def db_session():
    """
    Creates a fresh database session for a single test.
    """
    # Create tables (INCLUDING INDEXES from models.py)
    Base.metadata.create_all(bind=test_engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables to clean up
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    Overrides the dependency injection to use our test database.
    """
    def get_test_db_override():
        yield db_session
    
    def get_test_engine_override():
        yield test_engine

    app.dependency_overrides[get_db] = get_test_db_override
    app.dependency_overrides[get_engine] = get_test_engine_override
    
    # TestClient runs background tasks SYNCHRONOUSLY, which is great for testing.
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()

