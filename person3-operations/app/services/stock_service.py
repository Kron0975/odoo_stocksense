from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from app.database import products_collection, stock_ledger_collection


async def adjust_stock(
    product_id: str,
    location_id: str,
    change: float,
    movement_type: str,
    ref_id: str
) -> None:
    """
    Every stock mutation across Deliveries, Transfers, and Adjustments
    goes through this single function so the ledger stays consistent.

    Raises HTTPException 404 if the product/location combo doesn't exist.
    """
    # 1. Update product stock at that location
    result = await products_collection.update_one(
        {"_id": ObjectId(product_id), "stock_by_location.location_id": location_id},
        {"$inc": {"stock_by_location.$.quantity": change}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Product '{product_id}' not found at location '{location_id}'"
        )

    # 2. Log it in the shared ledger — every mutation leaves a trail
    await stock_ledger_collection.insert_one({
        "product_id": product_id,
        "location_id": location_id,
        "change": change,
        "type": movement_type,   # "Delivery" | "Transfer" | "Adjustment" | "Receipt"
        "ref_id": ref_id,
        "created_at": datetime.utcnow()
    })
