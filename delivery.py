from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DeliveryItem(BaseModel):
    product_id: str
    quantity: float
    location_id: str


class DeliveryCreate(BaseModel):
    delivery_number: str
    customer: str
    items: List[DeliveryItem]


class DeliveryOut(DeliveryCreate):
    id: str
    status: str = "Draft"
    created_at: datetime
    validated_at: Optional[datetime] = None
