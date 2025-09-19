# app/processing.py
import pandas as pd
from sqlalchemy.engine import Engine
import io

CHUNK_SIZE = 50_000  # Process 50,000 rows at a time

def validate_csv_format(file_contents: bytes):
    """
    Validates CSV format and structure without processing the entire file.
    
    Args:
        file_contents: The CSV file contents as bytes
        
    Raises:
        ValueError: If the CSV format is invalid
    """
    buffer = io.StringIO(file_contents.decode('utf-8'))
    
    try:
        # Read just the first few rows to validate structure
        sample_df = pd.read_csv(buffer, nrows=5)
        
        # Check for required columns
        required_cols = {"transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"}
        if not required_cols.issubset(sample_df.columns):
            missing_cols = required_cols - set(sample_df.columns)
            raise ValueError(f"CSV file is missing required columns: {', '.join(missing_cols)}")

        # Test numeric conversion on sample data
        pd.to_numeric(sample_df['transaction_amount'])
        
        # Test timestamp conversion on sample data
        pd.to_datetime(sample_df['timestamp'], format='mixed')
        
    except ValueError as e:
        raise ValueError(f"CSV file contains corrupt or malformed data: {e}")
    except Exception as e:
        raise ValueError(f"Invalid CSV format: {e}")

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
    
    try:
        # Use the 'chunksize' argument to create an iterator
        for chunk_df in pd.read_csv(buffer, chunksize=CHUNK_SIZE):
            # Check for required columns in the first chunk
            required_cols = {"transaction_id", "user_id", "product_id", "timestamp", "transaction_amount"}
            if not required_cols.issubset(chunk_df.columns):
                raise ValueError("CSV file is missing one or more required columns.")

            # Clean and transform data in the chunk if needed
            chunk_df['timestamp'] = pd.to_datetime(chunk_df['timestamp'], format='mixed')
            
            # This will raise a ValueError if conversion fails
            chunk_df['transaction_amount'] = pd.to_numeric(chunk_df['transaction_amount'])
            
            # Append the chunk to the database
            chunk_df.to_sql(
                'transactions', 
                con=engine, 
                if_exists='append',  # Use 'append' instead of 'replace'
                index=False
            )
            total_rows += len(chunk_df)
            
        return total_rows
    # Catch specific errors to provide better feedback
    except ValueError as e:
        # Re-raise with a more generic message for the API to catch
        raise ValueError(f"CSV file contains corrupt or malformed data: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred during CSV processing: {e}")

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

