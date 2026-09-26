from datetime import datetime
from bson import ObjectId
from app.database import products_collection, stock_ledger_collection


async def adjust_stock(product_id: str, location_id: str, change: float, movement_type: str, ref_id: str):
    """
    Every stock mutation across Deliveries, Transfers, and Adjustments
    goes through this single function so the ledger stays consistent.
    """
    # 1. Update product stock at that location
    await products_collection.update_one(
        {"_id": ObjectId(product_id), "stock_by_location.location_id": location_id},
        {"$inc": {"stock_by_location.$.quantity": change}}
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
