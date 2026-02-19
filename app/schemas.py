# app/schemas.py
from pydantic import BaseModel
from datetime import datetime, date

class TransactionBase(BaseModel):
    transaction_id: str
    user_id: int
    product_id: int
    timestamp: datetime
    transaction_amount: float

class SummaryStats(BaseModel):
    user_id: int
    max_transaction: float
    min_transaction: float
    mean_transaction: float

class SpendTrendItem(BaseModel):
    spend_date: date
    daily_total: float
    rolling_7d_avg: float

