from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field



class TransactionRequest(BaseModel):
    transaction_type: str = Field(max_length=3, min_length=3)
    currency: str = Field(min_length=3)
    quantity: float
    price_at_time: Optional[float] = None
    total_value: Optional[float] = None
    created_at: Optional[datetime] = None
