from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AdjustmentCreate(BaseModel):
    product_id: str
    location_id: str
    recorded_qty: float
    counted_qty: float
    reason: Optional[str] = None


class AdjustmentOut(AdjustmentCreate):
    id: str
    difference: float
    created_at: datetime
