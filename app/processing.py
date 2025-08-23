# app/processing.py
import pandas as pd
from sqlalchemy.engine import Engine
import io

CHUNK_SIZE = 50_000  # Process 50,000 rows at a time

def process_csv_to_db(file_contents: bytes, engine: Engine):
    """
    Processes a CSV file in chunks and appends data to the 'transactions' table.
    
    Args:
        file_contents: The CSV file contents as bytes
        engine: SQLAlchemy engine for database connection
        
    Returns:
        int: Total number of rows processed
    """
    buffer = io.StringIO(file_contents.decode('utf-8'))
    total_rows = 0
    
    # Use the 'chunksize' argument to create an iterator
    for chunk_df in pd.read_csv(buffer, chunksize=CHUNK_SIZE):
        # Clean and transform data in the chunk if needed
        chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'], format='mixed')
        
        # Append the chunk to the database
        chunk_df.to_sql(
            'transactions', 
            con=engine, 
            if_exists='append',  # Use 'append' instead of 'replace'
            index=False
        )
        total_rows += len(chunk_df)
        
    return total_rows

def create_database_indexes(engine: Engine):
    """
    Creates database indexes for better query performance.
    
    Args:
        engine: SQLAlchemy engine for database connection
    """
    try:
        with engine.connect() as connection:
            # Create index on user_id and timestamp for faster summary queries
            connection.execute("CREATE INDEX IF NOT EXISTS idx_user_timestamp ON transactions (user_id, timestamp)")
            connection.commit()
    except Exception as e:
        # Index might already exist or table might not exist yet
        pass