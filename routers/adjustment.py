from fastapi import APIRouter
from datetime import datetime

from app.database import adjustments_collection
from app.schemas.adjustment import AdjustmentCreate
from app.services.stock_service import adjust_stock

router = APIRouter(prefix="/api/adjustments", tags=["Adjustments"])


@router.post("/")
async def create_adjustment(payload: AdjustmentCreate):
    difference = payload.counted_qty - payload.recorded_qty

    doc = payload.dict()
    doc["difference"] = difference
    doc["created_at"] = datetime.utcnow()
    result = await adjustments_collection.insert_one(doc)

    # Apply the difference to stock immediately — no "Draft" pending step here
    await adjust_stock(
        product_id=payload.product_id,
        location_id=payload.location_id,
        change=difference,
        movement_type="Adjustment",
        ref_id=str(result.inserted_id)
    )

    return {"id": str(result.inserted_id), **doc}


@router.get("/")
async def get_adjustments():
    adjustments = await adjustments_collection.find().to_list(length=200)
    for a in adjustments:
        a["id"] = str(a["_id"])
        del a["_id"]
    return adjustments