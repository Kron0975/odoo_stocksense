from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TransferCreate(BaseModel):
    transfer_number: str
    product_id: str
    quantity: float
    from_location: str
    to_location: str


class TransferOut(TransferCreate):
    id: str
    status: str = "Draft"
    created_at: datetime
    validated_at: Optional[datetime] = None
