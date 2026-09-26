from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from app.database import deliveries_collection
from app.models.delivery import DeliveryCreate, DeliveryResponse
from app.services.stock_service import adjust_stock

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


@router.post("/", response_model=DeliveryResponse, status_code=201)
async def create_delivery(payload: DeliveryCreate):
    """
    Record an inbound delivery. Increases stock at the destination location.
    """
    doc = {
        "product_id": payload.product_id,
        "location_id": payload.location_id,
        "quantity": payload.quantity,
        "supplier": payload.supplier,
        "notes": payload.notes,
        "status": "received",
        "created_at": datetime.utcnow(),
    }

    result = await deliveries_collection.insert_one(doc)
    ref_id = str(result.inserted_id)

    # Positive change — stock arrives at location
    await adjust_stock(
        product_id=payload.product_id,
        location_id=payload.location_id,
        change=payload.quantity,
        movement_type="Delivery",
        ref_id=ref_id,
    )

    return DeliveryResponse(
        id=ref_id,
        **payload.model_dump(),
        status="received",
        created_at=doc["created_at"],
    )


@router.get("/", response_model=list[DeliveryResponse])
async def list_deliveries(limit: int = 50, skip: int = 0):
    """Return recent deliveries, newest first."""
    cursor = deliveries_collection.find().sort("created_at", -1).skip(skip).limit(limit)
    results = []
    async for doc in cursor:
        results.append(DeliveryResponse(
            id=str(doc["_id"]),
            product_id=doc["product_id"],
            location_id=doc["location_id"],
            quantity=doc["quantity"],
            supplier=doc.get("supplier"),
            notes=doc.get("notes"),
            status=doc["status"],
            created_at=doc["created_at"],
        ))
    return results


@router.get("/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(delivery_id: str):
    """Fetch a single delivery by its ID."""
    try:
        oid = ObjectId(delivery_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid delivery ID format")

    doc = await deliveries_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return DeliveryResponse(
        id=str(doc["_id"]),
        product_id=doc["product_id"],
        location_id=doc["location_id"],
        quantity=doc["quantity"],
        supplier=doc.get("supplier"),
        notes=doc.get("notes"),
        status=doc["status"],
        created_at=doc["created_at"],
    )
