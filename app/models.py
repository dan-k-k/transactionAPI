# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from .database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    product_id = Column(Integer)
    timestamp = Column(DateTime, index=True)
    transaction_amount = Column(Float)

    # Explicit multi-column index for performance
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )

