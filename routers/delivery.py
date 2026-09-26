from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from bson import ObjectId

from app.database import deliveries_collection
from app.schemas.delivery import DeliveryCreate
from app.services.stock_service import adjust_stock

router = APIRouter(prefix="/api/deliveries", tags=["Deliveries"])


@router.post("/")
async def create_delivery(payload: DeliveryCreate):
    doc = payload.dict()
    doc["status"] = "Draft"
    doc["created_at"] = datetime.utcnow()
    doc["validated_at"] = None
    result = await deliveries_collection.insert_one(doc)
    return {"id": str(result.inserted_id), **doc}


@router.get("/")
async def get_deliveries(status: str = Query(None), warehouse: str = Query(None)):
    query = {}
    if status:
        query["status"] = status
    if warehouse:
        query["items.location_id"] = warehouse

    deliveries = await deliveries_collection.find(query).to_list(length=200)
    for d in deliveries:
        d["id"] = str(d["_id"])
        del d["_id"]
    return deliveries


@router.patch("/{delivery_id}/validate")
async def validate_delivery(delivery_id: str):
    delivery = await deliveries_collection.find_one({"_id": ObjectId(delivery_id)})
    if not delivery:
        raise HTTPException(status_code=404, detail="Not found")
    if delivery["status"] == "Done":
        raise HTTPException(status_code=400, detail="Already validated")

    for item in delivery["items"]:
        await adjust_stock(
            product_id=item["product_id"],
            location_id=item["location_id"],
            change=-item["quantity"],       # stock DECREASES
            movement_type="Delivery",
            ref_id=delivery_id
        )

    await deliveries_collection.update_one(
        {"_id": ObjectId(delivery_id)},
        {"$set": {"status": "Done", "validated_at": datetime.utcnow()}}
    )
    return {"message": "Delivery validated", "id": delivery_id}
