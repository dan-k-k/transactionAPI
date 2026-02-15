# tests/conftest.py
import pytest
import os
import shutil

os.environ["PREFECT_TEST_MODE"] = "1"
os.environ["PREFECT_LOGGING_LEVEL"] = "ERROR"
os.environ["UPLOAD_DIR"] = "./test_shared_data"

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Import app and global variables
from app.main import app, get_engine, get_db
from app.database import Base

# 1. Determine DB URL
# Use a specific test database name to avoid wiping dev data
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://user:password@localhost:5432/test_transactions_db" 
)

# For environments providing 'postgres://'
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

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_uploads():
    yield
    # Runs after all tests are done
    if os.path.exists("./test_shared_data"):
        shutil.rmtree("./test_shared_data")
    
@pytest.fixture(scope="function")
def seed_db_data(db_session):
    """
    Directly seeds the test database with dummy data for API summary tests.
    """
    from app.processing import process_csv_to_db
    import tempfile

    csv_content = (
        "transaction_id,user_id,product_id,timestamp,transaction_amount\n"
        "550e8400-e29b-41d4-a716-446655440000,123,101,2025-01-15 10:00:00,100.50\n"
        "550e8400-e29b-41d4-a716-446655440001,123,102,2025-01-16 11:00:00,200.75\n"
        "550e8400-e29b-41d4-a716-446655440002,456,103,2025-01-17 12:00:00,50.00"
    )
    
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(csv_content)
        process_csv_to_db.fn(file_path=path, database_url=TEST_DATABASE_URL)
    finally:
        os.remove(path)

