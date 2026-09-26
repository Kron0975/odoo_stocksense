from fastapi import FastAPI

from routers import receipt, delivery, transfer, adjustment

app = FastAPI(title="StockSense API")

app.include_router(receipt.router)
app.include_router(delivery.router)
app.include_router(transfer.router)
app.include_router(adjustment.router)


@app.get("/")
async def root():
    return {"message": "StockSense API is running"}
