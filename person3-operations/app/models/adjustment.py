from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AdjustmentCreate(BaseModel):
    product_id: str
    location_id: str
    change: float             # positive = stock in, negative = stock out
    reason: str               # e.g. "Damaged", "Stocktake correction", "Expired"
    notes: Optional[str] = None


class AdjustmentResponse(BaseModel):
    id: str
    product_id: str
    location_id: str
    change: float
    reason: str
    notes: Optional[str]
    created_at: datetime
