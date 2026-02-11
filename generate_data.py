# generate_data.py
import csv
import random
import argparse # Import argparse
from pathlib import Path
from faker import Faker

# Setup argument parser
parser = argparse.ArgumentParser(description="Generate dummy transaction data.")
parser.add_argument("--rows", type=int, default=1000, help="Number of rows to generate")
args = parser.parse_args()

TRANSACTIONS = args.rows # Use the argument
HEADERS = ["transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"]

fake = Faker()
output_file = Path("dummy_transactions.csv")

with output_file.open(mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=HEADERS)
    writer.writeheader()
    for _ in range(TRANSACTIONS):
        writer.writerow({
            "transaction_id": fake.uuid4(),
            "user_id": fake.random_int(min=1, max=1000),
            "product_id": fake.random_int(min=1, max=500),
            "timestamp": fake.date_time_between(start_date="-1y", end_date="now"),
            "transaction_amount": round(random.uniform(5.0, 500.0), 2),
        })

