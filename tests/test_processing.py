# tests/test_processing.py
import pytest
import os
import tempfile
from sqlalchemy import text

from app.processing import process_csv_to_db
from tests.conftest import TEST_DATABASE_URL

def test_process_csv_to_db_success(db_session):
    csv_content = (
        "transaction_id,user_id,product_id,timestamp,transaction_amount\n"
        "550e8400-e29b-41d4-a716-446655440000,123,101,2025-01-15 10:00:00,100.50\n"
        "550e8400-e29b-41d4-a716-446655440001,456,102,2025-01-16 11:00:00,200.75"
    )
    
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(csv_content)
            
        total_rows = process_csv_to_db.fn(file_path=path, database_url=TEST_DATABASE_URL)
        assert total_rows == 2
        result = db_session.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
        assert result == 2
    finally:
        os.remove(path)

def test_csv_conflict_resolution(db_session):
    # same transaction_id twice
    csv_content = (
        "transaction_id,user_id,product_id,timestamp,transaction_amount\n"
        "11111111-1111-1111-1111-111111111111,123,101,2025-01-15 10:00:00,100.50\n"
        "11111111-1111-1111-1111-111111111111,999,999,2025-01-16 11:00:00,500.00"
    )
    
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(csv_content)
            
        process_csv_to_db.fn(file_path=path, database_url=TEST_DATABASE_URL)
        
        result = db_session.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
        assert result == 1
        
        user_id = db_session.execute(text("SELECT user_id FROM transactions")).scalar()
        assert user_id == 123 # kept the first one
    finally:
        os.remove(path)

def test_corrupt_csv_columns():
    csv = "transaction_id,user_id,product_id,transaction_amount\n1,2,3,100"
    
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(csv)
            
        with pytest.raises(Exception) as excinfo:
            process_csv_to_db.fn(file_path=path, database_url=TEST_DATABASE_URL)
            
        assert "missing required columns" in str(excinfo.value).lower()
    finally:
        os.remove(path)

