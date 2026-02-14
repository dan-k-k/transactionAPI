# tests/test_api.py
import pytest
import io
import tempfile
import os

from app.processing import process_csv_to_db
from tests.conftest import TEST_DATABASE_URL

# --- Fixtures specific to this file ---

@pytest.fixture(scope="function")
def populate_integration_data(db_session):
    """
    Bypasses the async API queue and calls the processing logic directly
    to populate the test database with dummy data for summary tests.
    """
    csv_content = (
        "transaction_id,user_id,product_id,timestamp,transaction_amount\n"
        "550e8400-e29b-41d4-a716-446655440000,123,101,2025-01-15 10:00:00,100.50\n"
        "550e8400-e29b-41d4-a716-446655440001,123,102,2025-01-16 11:00:00,200.75\n"
        "550e8400-e29b-41d4-a716-446655440002,456,103,2025-01-17 12:00:00,50.00"
    )
    
    # Create a temporary physical file since the processor now expects a file path
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(csv_content)
            
        # Call the underlying function (.fn extracts it from the Prefect @task wrapper)
        process_csv_to_db.fn(file_path=path, database_url=TEST_DATABASE_URL)
    finally:
        os.remove(path) # Clean up the temp file

# --- Tests ---

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from the automated cloud!"}

def test_upload_csv_success(client):
    csv_content = "transaction_id,user_id,product_id,timestamp,transaction_amount\n" \
                  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11,1,101,2025-01-15 10:00:00,100.50"
    file_bytes = io.BytesIO(csv_content.encode('utf-8'))
    
    response = client.post(
        "/upload", 
        files={"file": ("test.csv", file_bytes, "text/csv")}
    )

    assert response.status_code == 200
    # Update: Look for "queued" instead of "accepted"
    assert "queued" in response.json()["message"]

def test_get_summary_success(client, populate_integration_data):
    response = client.get("/summary/123?start_date=2025-01-01&end_date=2025-12-31")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 123
    assert data["max_transaction"] == 200.75
    assert data["min_transaction"] == 100.50
    assert abs(data["mean_transaction"] - 150.625) < 0.001

def test_get_summary_date_filtering(client, populate_integration_data):
    response = client.get("/summary/123?start_date=2025-01-14&end_date=2025-01-15")
    assert response.status_code == 200
    assert response.json()["max_transaction"] == 100.50 

def test_get_summary_not_found(client, populate_integration_data):
    response = client.get("/summary/9999?start_date=2025-01-01&end_date=2025-12-31")
    assert response.status_code == 404

def test_get_summary_bad_date_logic(client):
    response = client.get("/summary/1?start_date=2025-02-01&end_date=2025-01-01")
    assert response.status_code == 400

def test_invalid_file_type(client):
    response = client.post(
        "/upload", 
        files={"file": ("test.txt", io.BytesIO(b"data"), "text/plain")}
    )
    assert response.status_code == 400

def test_corrupt_csv_columns():
    # Update: Test the processor logic directly, since the API just blindly queues it now
    csv = "transaction_id,user_id,product_id,transaction_amount\n1,2,3,100"
    
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(csv)
            
        # Expect the processor to raise an Exception for missing columns
        with pytest.raises(Exception) as excinfo:
            process_csv_to_db.fn(file_path=path, database_url=TEST_DATABASE_URL)
            
        assert "missing required columns" in str(excinfo.value).lower()
    finally:
        os.remove(path)

