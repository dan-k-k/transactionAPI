# tests/test_api.py
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

def test_get_risk_profile_success(client, seed_db_data):
    response = client.get("/analytics/risk-profile/123")
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_id"] == 123
    assert "risk_metrics" in data
    metrics = data["risk_metrics"]
    
    # Seeded user 123 with two transactions ($100.50 and $200.75) exactly 25 hours apart
    assert metrics["total_lifetime_spend"] == 301.25
    assert metrics["shortest_time_between_transactions_mins"] == 1500.0 # 25 hours * 60 mins
    assert metrics["max_single_transaction_spike"] == 200.75
    assert "spending_volatility_index" in metrics

def test_get_risk_profile_not_found(client, seed_db_data):
    response = client.get("/analytics/risk-profile/9999")
    assert response.status_code == 404

def test_get_spend_trend_gap_fill(client, db_session):
    """
    Directly insert transactions with a missing day in between to 
    ensure the SQL query successfully generates a $0 row for the missing day.
    """
    from sqlalchemy import text
    
    # Insert a transaction on Jan 1st and Jan 3rd (Skipping Jan 2nd)
    db_session.execute(text("""
        INSERT INTO transactions (transaction_id, user_id, product_id, timestamp, transaction_amount)
        VALUES 
        ('11111111-1111-1111-1111-111111111111', 777, 1, '2025-01-01 10:00:00', 100.00),
        ('22222222-2222-2222-2222-222222222222', 777, 2, '2025-01-03 10:00:00', 200.00)
    """))
    db_session.commit()

    response = client.get("/analytics/spend-trend/777")
    assert response.status_code == 200
    data = response.json()
    
    # Should have 3 days: Jan 1, Jan 2, Jan 3
    assert len(data) == 3
    
    # Verify Jan 1
    assert data[0]["spend_date"] == "2025-01-01"
    assert data[0]["daily_total"] == 100.0
    assert data[0]["rolling_7d_avg"] == 100.0
    
    # Verify Jan 2 (The Gap Day)
    assert data[1]["spend_date"] == "2025-01-02"
    assert data[1]["daily_total"] == 0.0
    assert data[1]["rolling_7d_avg"] == 50.0  # (100 + 0) / 2 days
    
    # Verify Jan 3
    assert data[2]["spend_date"] == "2025-01-03"
    assert data[2]["daily_total"] == 200.0
    assert data[2]["rolling_7d_avg"] == 100.0 # (100 + 0 + 200) / 3 days

def test_get_spend_trend_not_found(client):
    response = client.get("/analytics/spend-trend/9999")
    assert response.status_code == 404

def test_get_dashboard_success(client, seed_db_data):
    response = client.get("/dashboard/123")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    html = response.text
    # Verify it actually loaded Plotly and our specific graph title
    assert "plotly" in html.lower()
    assert "Transaction Analysis: User 123" in html

def test_get_dashboard_no_data(client):
    response = client.get("/dashboard/9999")
    assert response.status_code == 404
    assert "No data available to plot" in response.text

