from motor.motor_asyncio import AsyncIOMotorClient

# --- MongoDB connection ---
client = AsyncIOMotorClient("mongodb://localhost:27017/")
db = client["stocksense"]

# --- Collections used across all modules ---
suppliers_collection = db["suppliers"]
products_collection = db["products"]
receipts_collection = db["receipts"]
deliveries_collection = db["deliveries"]
transfers_collection = db["transfers"]
adjustments_collection = db["adjustments"]
stock_ledger_collection = db["stock_ledger"]
