import uvicorn
from fastapi import FastAPI
from .otp_router import router as otp_router

app = FastAPI(title="OTP Service")
app.include_router(otp_router)

if __name__ == "__main__":
    uvicorn.run("otp_service.main:app", host="0.0.0.0", port=8004, reload=True)

