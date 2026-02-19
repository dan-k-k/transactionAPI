# app/processing.py
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert 
import os
from prefect import task, flow

CHUNK_SIZE = 5_000

def insert_on_conflict_nothing(table, conn, keys, data_iter): # If the transaction_id already exists, skip it
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(data)
    stmt = stmt.on_conflict_do_nothing(index_elements=['transaction_id'])
    conn.execute(stmt)

@task(retries=3, retry_delay_seconds=10)
def process_csv_to_db(file_path: str, database_url: str):
    # Spin up the engine *inside* the task
    engine = create_engine(database_url)
    total_rows = 0
    
    with engine.begin() as connection:
        try:

            for chunk_df in pd.read_csv(file_path, chunksize=CHUNK_SIZE):
                required_cols = {"transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"}
                if not required_cols.issubset(chunk_df.columns):
                    raise ValueError("CSV missing required columns.")

                chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'], format='mixed')
                chunk_df['transaction_amount'] = pd.to_numeric(chunk_df['transaction_amount'])
                
                chunk_df.to_sql('transactions', con=connection, if_exists='append', index=False, method=insert_on_conflict_nothing) 
                total_rows += len(chunk_df)
                
            return total_rows
        except Exception as e:
            raise Exception(f"CSV processing failed: {e}")

@flow(name="CSV Ingestion Pipeline")
def run_csv_pipeline(file_path: str, database_url: str):
    process_csv_to_db(file_path, database_url)
    if os.path.exists(file_path):
        os.remove(file_path)

