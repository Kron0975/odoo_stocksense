from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DeliveryCreate(BaseModel):
    product_id: str
    location_id: str          # destination warehouse/location
    quantity: float
    supplier: Optional[str] = None
    notes: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: str
    product_id: str
    location_id: str
    quantity: float
    supplier: Optional[str]
    notes: Optional[str]
    status: str
    created_at: datetime
