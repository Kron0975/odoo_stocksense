from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TransferCreate(BaseModel):
    product_id: str
    from_location_id: str
    to_location_id: str
    quantity: float = Field(gt=0, description="Must be greater than zero")
    notes: Optional[str] = None


class TransferResponse(BaseModel):
    id: str
    product_id: str
    from_location_id: str
    to_location_id: str
    quantity: float
    notes: Optional[str]
    status: str
    created_at: datetime
