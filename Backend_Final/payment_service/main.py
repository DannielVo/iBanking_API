import uvicorn
from fastapi import FastAPI
from .payment_router import router as payment_router

app = FastAPI(title="Payment Service")
app.include_router(payment_router)

if __name__ == "__main__":
    uvicorn.run("payment_service.main:app", host="0.0.0.0", port=8003, reload=True)
