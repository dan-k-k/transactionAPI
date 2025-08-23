# tests/test_api.py
import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_engine, get_db
from app.database import SessionLocal

# --- ADD THESE IMPORTS ---
import sqlite3
from datetime import date
from sqlalchemy.event import listen
# -------------------------

# --- Test Setup ---
# Use a clean, in-memory SQLite database for all tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# --- ADD THIS FUNCTION AND THE LISTENER ---
# This function will be called for every new connection made by the test_engine
def _fk_pragma_on_connect_test(dbapi_con, con_record):
    """Registers the date adapter for the test SQLite connection."""
    sqlite3.register_adapter(date, lambda val: val.isoformat())

# Apply the listener directly to the test_engine
listen(test_engine, 'connect', _fk_pragma_on_connect_test)
# ----------------------------------------

# Create a test session
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override dependencies
def get_test_engine():
    yield test_engine

def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_engine] = get_test_engine
app.dependency_overrides[get_db] = get_test_db

# --- Fixtures ---
@pytest.fixture(scope="module")
def client():
    """Create a test client that all tests can use."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db_with_data(client):
    """Set up the database with test data for tests that need it."""
    csv_content = (
        "transaction_id,user_id,product_id,timestamp,transaction_amount\n"
        "uuid1,123,101,2025-01-15 10:00:00,100.50\n"
        "uuid2,123,102,2025-01-16 11:00:00,200.75\n"
        "uuid3,456,103,2025-01-17 12:00:00,50.00"
    )
    # Using BytesIO is cleaner than creating a physical file
    file_bytes = io.BytesIO(csv_content.encode('utf-8'))
    response = client.post("/upload", files={"file": ("test_data.csv", file_bytes, "text/csv")})
    
    # Wait a moment for background processing to complete
    # In a real application, you might want to check if processing is complete
    import time
    time.sleep(0.1)
    
    return response

# --- Tests ---
def test_read_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Transaction Analysis API"}

def test_upload_csv_success(client):
    """Test successful CSV upload."""
    csv_content = "transaction_id,user_id,product_id,timestamp,transaction_amount\n" \
                  "uuid1,1,101,2025-01-15 10:00:00,100.50\n" \
                  "uuid2,2,102,2025-01-16 11:00:00,200.75"

    file_bytes = io.BytesIO(csv_content.encode('utf-8'))
    response = client.post("/upload", files={"file": ("test_transactions.csv", file_bytes, "text/csv")})

    assert response.status_code == 200
    assert "accepted and is being processed" in response.json()["message"]

def test_upload_invalid_file_type(client):
    """Test upload with invalid file type."""
    file_bytes = io.BytesIO(b"not a csv")
    response = client.post("/upload", files={"file": ("test.txt", file_bytes, "text/plain")})
    
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_get_summary_success(client, db_with_data):
    """Test successful summary retrieval."""
    response = client.get("/summary/123?start_date=2025-01-01&end_date=2025-12-31")
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 123
    assert data["max_transaction"] == 200.75
    assert data["min_transaction"] == 100.50

def test_get_summary_not_found(client, db_with_data):
    """Test summary for non-existent user."""
    response = client.get("/summary/9999?start_date=2025-01-01&end_date=2025-12-31")
    
    assert response.status_code == 404
    assert "No transactions found" in response.json()["detail"]

def test_get_summary_invalid_date_range(client):
    """Test summary with invalid date format."""
    response = client.get("/summary/1?start_date=invalid&end_date=2025-01-01")
    assert response.status_code == 422  # Validation error