# app/models.py
from pydantic import BaseModel

class SummaryStats(BaseModel):
    user_id: int
    max_transaction: float
    min_transaction: float
    mean_transaction: float

