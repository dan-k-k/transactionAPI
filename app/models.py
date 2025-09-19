# app/models.py
from pydantic import BaseModel

#for the api response
class SummaryStats(BaseModel):
    user_id: int
    max_transaction: float
    min_transaction: float
    mean_transaction: float

