# scripts/stress_test.py
import requests
import time
import pandas as pd
import numpy as np
import os
import uuid 

# Configuration
API_URL = "http://localhost:8000/upload"
NUM_ROWS = 10_000_000  # Large enough to trigger multiple chunks of 50k
FILENAME = "large_test_file.csv"

def generate_large_csv():
    print(f"Generating {NUM_ROWS} rows of dummy data...")
    
    df = pd.DataFrame({
        'transaction_id': [str(uuid.uuid4()) for _ in range(NUM_ROWS)],
        'user_id': np.random.randint(1, 1000, NUM_ROWS),
        'product_id': np.random.randint(1, 500, NUM_ROWS),
        'timestamp': pd.date_range(start='1/1/2024', periods=NUM_ROWS, freq='min'),
        'transaction_amount': np.random.uniform(10, 1000, NUM_ROWS).round(2)
    })
    
    df.to_csv(FILENAME, index=False)
    file_size_mb = os.path.getsize(FILENAME) / (1024 * 1024)
    print(f"File generated: {file_size_mb:.2f} MB")

def test_upload_performance():
    generate_large_csv()
    
    print("Uploading file to API...")
    start_time = time.time()
    
    with open(FILENAME, 'rb') as f:
        files = {'file': (FILENAME, f, 'text/csv')}
        response = requests.post(API_URL, files=files)
    
    end_time = time.time()
    duration = end_time - start_time
    
    if response.status_code == 200:
        print(f"Success! API accepted the file in {duration:.2f} seconds.")
        print(f"Response: {response.json()}")
    else:
        print(f"Failed. Status: {response.status_code}")
        print(f"Response: {response.text}")
    
    os.remove(FILENAME)

if __name__ == "__main__":
    try:
        # Check if the server is running
        requests.get("http://localhost:8000/")
        test_upload_performance()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API.")
        print("Make sure the app is running: 'uvicorn app.main:app --reload'")

