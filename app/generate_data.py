# app/generate_data.py
import csv
import random
import uuid
# Remove 'os' if not used, keep 'pathlib'
from pathlib import Path
from faker import Faker
from datetime import datetime, timedelta
from prefect import task, flow
from app.processing import run_csv_pipeline 
from app.config import settings

@task
def generate_daily_batch(rows: int = 150):
    filename_str = f"daily_batch_{uuid.uuid4()}.csv"
    file_path = Path("/shared_data") / filename_str
    
    fake = Faker()
    
    yesterday_start = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0)
    yesterday_end = yesterday_start.replace(hour=23, minute=59, second=59)

    print(f"Generating {rows} rows for {yesterday_start.date()} into {file_path}...")

    with open(file_path, mode="w", newline="") as file:
        headers = ["transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"]
        writer = csv.DictWriter(file, fieldnames=headers)
        
        writer.writeheader()
            
        for _ in range(rows):
            writer.writerow({
                "transaction_id": fake.uuid4(),
                "user_id": fake.random_int(min=1, max=1000),
                "product_id": fake.random_int(min=1, max=500),
                "timestamp": fake.date_time_between(start_date=yesterday_start, end_date=yesterday_end),
                "transaction_amount": round(random.uniform(5.0, 500.0), 2),
            })

    return str(file_path)

@flow(name="Nightly Data Generator")
def run_nightly_generation():
    daily_file_path = generate_daily_batch()
    run_csv_pipeline(file_path=daily_file_path, database_url=settings.get_database_url())

if __name__ == "__main__":
    # cron string "1 0 * * *" means 12:01 AM every day
    run_nightly_generation.serve(
        name="daily-append-job",
        tags=["generation", "cron"],
        cron="1 0 * * *", 
        description="Generates yesterday's dummy transactions and uploads to DB."
    )

