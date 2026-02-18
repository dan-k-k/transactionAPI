# tests/test_api.py
import pytest
import io
from unittest.mock import patch, AsyncMock

# --- Tests ---

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from the automated cloud!"}

# @patch to intercept the call to run_deployment so it doesn't actually try to reach Prefect
@patch("app.main.run_deployment", new_callable=AsyncMock) 
def test_upload_csv_success(mock_run_deployment, client):
    csv_content = "transaction_id,user_id,product_id,timestamp,transaction_amount\n" \
                  "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11,1,101,2025-01-15 10:00:00,100.50"
    file_bytes = io.BytesIO(csv_content.encode('utf-8'))
    
    response = client.post(
        "/upload", 
        files={"file": ("test.csv", file_bytes, "text/csv")}
    )

    assert response.status_code == 200
    assert "queued" in response.json()["message"]
    mock_run_deployment.assert_called_once()

def test_invalid_file_type(client):
    response = client.post(
        "/upload", 
        files={"file": ("test.txt", io.BytesIO(b"data"), "text/plain")}
    )
    assert response.status_code == 400

# Client to test the API layer; rely on a fixture to seed the DB.
def test_get_summary_success(client, seed_db_data):
    response = client.get("/summary/123?start_date=2025-01-01&end_date=2025-12-31")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 123
    assert data["max_transaction"] == 200.75
    assert data["min_transaction"] == 100.50
    assert abs(data["mean_transaction"] - 150.625) < 0.001

def test_get_summary_date_filtering(client, seed_db_data):
    response = client.get("/summary/123?start_date=2025-01-14&end_date=2025-01-15")
    assert response.status_code == 200
    assert response.json()["max_transaction"] == 100.50 

def test_get_summary_not_found(client, seed_db_data):
    response = client.get("/summary/9999?start_date=2025-01-01&end_date=2025-12-31")
    assert response.status_code == 404

def test_get_summary_bad_date_logic(client):
    response = client.get("/summary/1?start_date=2025-02-01&end_date=2025-01-01")
    assert response.status_code == 400

