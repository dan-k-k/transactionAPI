# app/gen_bulk.py
import csv
import random
import uuid
from pathlib import Path
from faker import Faker
from prefect import task, flow
from app.processing import run_csv_pipeline 
from app.config import settings

@task
def generate_bulk_csv(rows: int):
    filename_str = f"bulk_batch_{uuid.uuid4()}.csv"
    # Save directly to the EC2 shared volume
    file_path = Path("/shared_data") / filename_str 
    
    fake = Faker()
    print(f"Generating {rows} rows into {file_path}...")

    with open(file_path, mode="w", newline="") as file:
        headers = ["transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"]
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        for _ in range(rows):
            writer.writerow({
                "transaction_id": fake.uuid4(),
                "user_id": fake.random_int(min=1, max=1000),
                "product_id": fake.random_int(min=1, max=500),
                "timestamp": fake.date_time_between(start_date="-1y", end_date="now"),
                "transaction_amount": round(random.uniform(5.0, 500.0), 2),  # nosec B311
            })

    return str(file_path)

@flow(name="Bulk Data Generator Pipeline")
def run_bulk_generation(num_rows: int = 10000):
    """
    Generates a specified number of dummy transactions and ingests them into the database.
    """
    file_path = generate_bulk_csv(rows=num_rows)
    run_csv_pipeline(file_path=file_path, database_url=settings.get_database_url())

