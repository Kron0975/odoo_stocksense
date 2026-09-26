from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client["stocksense"]

deliveries_collection = db["deliveries"]
transfers_collection = db["transfers"]
adjustments_collection = db["adjustments"]
stock_ledger_collection = db["stock_ledger"]   # shared with Person 2
products_collection = db["products"]           # owned by Person 1
