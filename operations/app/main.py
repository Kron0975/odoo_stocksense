from fastapi import FastAPI
from app.routers import adjustment, delivery, transfer

app = FastAPI(
    title="StockSense Operations API",
    description="Handles Deliveries, Transfers, and Stock Adjustments (Person 3).",
    version="1.0.0",
)

app.include_router(delivery.router)
app.include_router(transfer.router)
app.include_router(adjustment.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
