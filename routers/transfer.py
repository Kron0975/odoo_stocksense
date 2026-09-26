from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from app.database import transfers_collection
from app.schemas.transfer import TransferCreate
from app.services.stock_service import adjust_stock

router = APIRouter(prefix="/api/transfers", tags=["Transfers"])


@router.post("/")
async def create_transfer(payload: TransferCreate):
    doc = payload.dict()
    doc["status"] = "Draft"
    doc["created_at"] = datetime.utcnow()
    doc["validated_at"] = None
    result = await transfers_collection.insert_one(doc)
    return {"id": str(result.inserted_id), **doc}


@router.get("/")
async def get_transfers():
    transfers = await transfers_collection.find().to_list(length=200)
    for t in transfers:
        t["id"] = str(t["_id"])
        del t["_id"]
    return transfers


@router.patch("/{transfer_id}/validate")
async def validate_transfer(transfer_id: str):
    transfer = await transfers_collection.find_one({"_id": ObjectId(transfer_id)})
    if not transfer:
        raise HTTPException(status_code=404, detail="Not found")
    if transfer["status"] == "Done":
        raise HTTPException(status_code=400, detail="Already validated")

    # Total stock unchanged — decrease at source, increase at destination
    await adjust_stock(
        product_id=transfer["product_id"],
        location_id=transfer["from_location"],
        change=-transfer["quantity"],
        movement_type="Transfer",
        ref_id=transfer_id
    )
    await adjust_stock(
        product_id=transfer["product_id"],
        location_id=transfer["to_location"],
        change=transfer["quantity"],
        movement_type="Transfer",
        ref_id=transfer_id
    )

    await transfers_collection.update_one(
        {"_id": ObjectId(transfer_id)},
        {"$set": {"status": "Done", "validated_at": datetime.utcnow()}}
    )
    return {"message": "Transfer validated", "id": transfer_id}
