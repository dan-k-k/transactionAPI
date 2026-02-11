# tests/test_api.py
import pytest
import io

# --- Fixtures specific to this file ---

@pytest.fixture(scope="function")
def populate_integration_data(client):
    """
    Uses the API itself to upload data, verifying the full 'Upload -> DB' pipeline.
    Because TestClient is synchronous, the data is guaranteed to be in the DB 
    before the test function starts.
    """
    csv_content = (
        "transaction_id,user_id,product_id,timestamp,transaction_amount\n"
        "uuid1,123,101,2025-01-15 10:00:00,100.50\n"
        "uuid2,123,102,2025-01-16 11:00:00,200.75\n"
        "uuid3,456,103,2025-01-17 12:00:00,50.00"
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
    assert response.json() == {"message": "Welcome to the Transaction Analysis API"}

def test_upload_csv_success(client):
    csv_content = "transaction_id,user_id,product_id,timestamp,transaction_amount\n" \
                  "uuid_new,1,101,2025-01-15 10:00:00,100.50"
    file_bytes = io.BytesIO(csv_content.encode('utf-8'))
    
    response = client.post(
        "/upload", 
        files={"file": ("test.csv", file_bytes, "text/csv")}
    )
    
    assert response.status_code == 200
    assert "accepted" in response.json()["message"]

def test_get_summary_success(client, populate_integration_data):
    # This test relies on populate_integration_data to have finished inserting rows
    response = client.get("/summary/123?start_date=2025-01-01&end_date=2025-12-31")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify math
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
    assert data["max_transaction"] == 100.50 # The 200.75 transaction was on the 16th

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
    csv = "transaction_id,user_id,product_id,transaction_amount\n1,2,3,100"
    response = client.post(
        "/upload", 
        files={"file": ("bad.csv", io.BytesIO(csv.encode()), "text/csv")}
    )
    assert response.status_code == 400
    assert "missing required columns" in response.json()["detail"]

