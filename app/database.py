# app/database.py
import sqlite3
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listen

# This is the connection string for a local SQLite database file named 'transactions.db'
DATABASE_URL = "sqlite:///./transactions.db"

# The engine is the main entry point to the database.
# 'connect_args' is only needed for SQLite to allow it to be used by multiple threads,
# which is what FastAPI does.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This ensures that Python date objects are handled correctly by sqlite3
# in Python 3.12+ to avoid the DeprecationWarning.
def _fk_pragma_on_connect(dbapi_con, con_record):
    """Ensures that the foreign key pragma is enabled for SQLite connections."""
    dbapi_con.execute('PRAGMA foreign_keys=ON')
    # Register the adapter for date objects
    sqlite3.register_adapter(date, lambda val: val.isoformat())

# Use the listen function from SQLAlchemy to apply this to every new connection
listen(engine, 'connect', _fk_pragma_on_connect)

