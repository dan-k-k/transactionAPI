# app/models.py
from sqlalchemy import Column, Integer, DateTime, Index, DECIMAL 
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, index=True)
    product_id = Column(Integer)
    timestamp = Column(DateTime, index=True)
    transaction_amount = Column(DECIMAL(10, 2))

    # Explicit multi-column index for performance
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )

