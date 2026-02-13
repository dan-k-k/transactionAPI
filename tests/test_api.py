# tests/test_api.py
import pytest
import io
import uuid 

# --- Fixtures specific to this file ---

@pytest.fixture(scope="function")
def populate_integration_data(client):
    """
    Uses the API itself to upload data, verifying the full 'Upload -> DB' pipeline.
    We use VALID UUIDs here to satisfy the Postgres UUID type constraint.
    """
    csv_content = (
        "transaction_id,user_id,product_id,timestamp,transaction_amount\n"
        "550e8400-e29b-41d4-a716-446655440000,123,101,2025-01-15 10:00:00,100.50\n"
        "550e8400-e29b-41d4-a716-446655440001,123,102,2025-01-16 11:00:00,200.75\n"
        "550e8400-e29b-41d4-a716-446655440002,456,103,2025-01-17 12:00:00,50.00"
    )
    file_bytes = io.BytesIO(csv_content.encode('utf-8'))
    response = client.post(
        "/upload", 
        files={"file": ("integration_test_data.csv", file_bytes, "text/csv")}
    )
    assert response.status_code == 200
    return response

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
    
    # Debugging tip: If this fails, print response.json() to see why
    if response.status_code != 200:
        print(f"Upload failed: {response.json()}")

    assert response.status_code == 200
    assert "accepted" in response.json()["message"]

def test_get_summary_success(client, populate_integration_data):
    # This test relies on populate_integration_data to have finished inserting rows
    response = client.get("/summary/123?start_date=2025-01-01&end_date=2025-12-31")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify maths
    assert data["user_id"] == 123
    assert data["max_transaction"] == 200.75  # Max of 100.50 and 200.75
    assert data["min_transaction"] == 100.50
    # Floating point comparison (approximate)
    assert abs(data["mean_transaction"] - 150.625) < 0.001

def test_get_summary_date_filtering(client, populate_integration_data):
    # Test that date filters actually work (Should only find the Jan 15th transaction)
    response = client.get("/summary/123?start_date=2025-01-14&end_date=2025-01-15")
    
    assert response.status_code == 200
    data = response.json()
    # The fixture has 100.50 on Jan 15, and 200.75 on Jan 16.
    # Filter ends on Jan 15, so max should be 100.50.
    assert data["max_transaction"] == 100.50 

def test_get_summary_not_found(client, populate_integration_data):
    # User 9999 does not exist
    response = client.get("/summary/9999?start_date=2025-01-01&end_date=2025-12-31")
    assert response.status_code == 404

def test_get_summary_bad_date_logic(client):
    # Start date after end date
    response = client.get("/summary/1?start_date=2025-02-01&end_date=2025-01-01")
    assert response.status_code == 400

def test_invalid_file_type(client):
    response = client.post(
        "/upload", 
        files={"file": ("test.txt", io.BytesIO(b"data"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_corrupt_csv_columns(client):
    # Missing 'timestamp' column
    # Even corrupt CSVs need a valid UUID in the first column to pass the initial regex
    csv = "transaction_id,user_id,product_id,transaction_amount\n1,2,3,100"
    response = client.post(
        "/upload", 
        files={"file": ("bad.csv", io.BytesIO(csv.encode()), "text/csv")}
    )
    assert response.status_code == 400
    assert "missing required columns" in response.json()["detail"]

