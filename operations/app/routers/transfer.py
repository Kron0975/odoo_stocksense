from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from bson import ObjectId

from app.database import transfers_collection
from app.models.transfer import TransferCreate, TransferResponse
from app.services.stock_service import adjust_stock

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post("/", response_model=TransferResponse, status_code=201)
async def create_transfer(payload: TransferCreate):
    """
    Move stock from one location to another.
    Decrements source, increments destination — both ledger entries written.
    If destination update fails, source deduction is automatically reversed.
    """
    if payload.from_location_id == payload.to_location_id:
        raise HTTPException(
            status_code=400,
            detail="Source and destination locations must be different"
        )

    now = datetime.now(timezone.utc)

    # Insert transfer record
    doc = {
        "product_id": payload.product_id,
        "from_location_id": payload.from_location_id,
        "to_location_id": payload.to_location_id,
        "quantity": payload.quantity,
        "notes": payload.notes,
        "status": "completed",
        "created_at": now,
    }
    result = await transfers_collection.insert_one(doc)
    ref_id = str(result.inserted_id)

    # Step 1: Deduct from source location
    try:
        await adjust_stock(
            product_id=payload.product_id,
            location_id=payload.from_location_id,
            change=-payload.quantity,
            movement_type="Transfer",
            ref_id=ref_id,
        )
    except ValueError as e:
        await transfers_collection.delete_one({"_id": ObjectId(ref_id)})
        raise HTTPException(status_code=404, detail=str(e))

    # Step 2: Add to destination — if this fails, reverse the source deduction
    try:
        await adjust_stock(
            product_id=payload.product_id,
            location_id=payload.to_location_id,
            change=payload.quantity,
            movement_type="Transfer",
            ref_id=ref_id,
        )
    except ValueError as e:
        # Compensate: reverse the source deduction to avoid stock loss
        await adjust_stock(
            product_id=payload.product_id,
            location_id=payload.from_location_id,
            change=payload.quantity,   # put it back
            movement_type="Transfer_Reversal",
            ref_id=ref_id,
        )
        await transfers_collection.delete_one({"_id": ObjectId(ref_id)})
        raise HTTPException(
            status_code=404,
            detail=f"Destination location error: {e}. Transfer reversed."
        )

    return TransferResponse(
        id=ref_id,
        **payload.model_dump(),
        status="completed",
        created_at=now,
    )


@router.get("/", response_model=list[TransferResponse])
async def list_transfers(limit: int = 50, skip: int = 0):
    """Return recent transfers, newest first."""
    cursor = transfers_collection.find().sort("created_at", -1).skip(skip).limit(limit)
    results = []
    async for doc in cursor:
        results.append(TransferResponse(
            id=str(doc["_id"]),
            product_id=doc["product_id"],
            from_location_id=doc["from_location_id"],
            to_location_id=doc["to_location_id"],
            quantity=doc["quantity"],
            notes=doc.get("notes"),
            status=doc["status"],
            created_at=doc["created_at"],
        ))
    return results


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(transfer_id: str):
    """Fetch a single transfer by its ID."""
    try:
        oid = ObjectId(transfer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid transfer ID format")

    doc = await transfers_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Transfer not found")

    return TransferResponse(
        id=str(doc["_id"]),
        product_id=doc["product_id"],
        from_location_id=doc["from_location_id"],
        to_location_id=doc["to_location_id"],
        quantity=doc["quantity"],
        notes=doc.get("notes"),
        status=doc["status"],
        created_at=doc["created_at"],
    )
