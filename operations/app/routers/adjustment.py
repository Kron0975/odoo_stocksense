from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from bson import ObjectId

from app.database import adjustments_collection
from app.models.adjustment import AdjustmentCreate, AdjustmentResponse
from app.services.stock_service import adjust_stock

router = APIRouter(prefix="/adjustments", tags=["Adjustments"])


@router.post("/", response_model=AdjustmentResponse, status_code=201)
async def create_adjustment(payload: AdjustmentCreate):
    """
    Record a manual stock adjustment (e.g. damage write-off, stocktake correction).
    A positive `change` adds stock; a negative `change` removes stock.
    DB record is rolled back if stock update fails.
    """
    now = datetime.now(timezone.utc)

    doc = {
        "product_id": payload.product_id,
        "location_id": payload.location_id,
        "change": payload.change,
        "reason": payload.reason,
        "notes": payload.notes,
        "created_at": now,
    }
    result = await adjustments_collection.insert_one(doc)
    ref_id = str(result.inserted_id)

    # Mutate stock and write to shared ledger
    try:
        await adjust_stock(
            product_id=payload.product_id,
            location_id=payload.location_id,
            change=payload.change,
            movement_type="Adjustment",
            ref_id=ref_id,
        )
    except ValueError as e:
        # Roll back the adjustment record since stock update failed
        await adjustments_collection.delete_one({"_id": ObjectId(ref_id)})
        raise HTTPException(status_code=404, detail=str(e))

    return AdjustmentResponse(
        id=ref_id,
        **payload.model_dump(),
        created_at=now,
    )


@router.get("/", response_model=list[AdjustmentResponse])
async def list_adjustments(limit: int = 50, skip: int = 0):
    """Return recent adjustments, newest first."""
    cursor = adjustments_collection.find().sort("created_at", -1).skip(skip).limit(limit)
    results = []
    async for doc in cursor:
        results.append(AdjustmentResponse(
            id=str(doc["_id"]),
            product_id=doc["product_id"],
            location_id=doc["location_id"],
            change=doc["change"],
            reason=doc["reason"],
            notes=doc.get("notes"),
            created_at=doc["created_at"],
        ))
    return results


@router.get("/{adjustment_id}", response_model=AdjustmentResponse)
async def get_adjustment(adjustment_id: str):
    """Fetch a single adjustment by its ID."""
    try:
        oid = ObjectId(adjustment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid adjustment ID format")

    doc = await adjustments_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Adjustment not found")

    return AdjustmentResponse(
        id=str(doc["_id"]),
        product_id=doc["product_id"],
        location_id=doc["location_id"],
        change=doc["change"],
        reason=doc["reason"],
        notes=doc.get("notes"),
        created_at=doc["created_at"],
    )
