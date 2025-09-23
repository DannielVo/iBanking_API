from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import pyodbc
from datetime import datetime, timedelta
import random

app = FastAPI(title="OTP Service")

# ================== Logging Config ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ================== Global Exception Handler ==================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error. Please try again later."})

# ================== DB Connection ==================
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=ADIDAPHAT\\MSSQLSERVER01;"
        "DATABASE=OtpDB;"
        "Trusted_Connection=yes;"
    )

# ================== Models ==================
class OTPVerifyRequest(BaseModel):
    userId: int
    otpCode: str

# ================== Endpoints ==================
@app.post("/otp/generate")
def generate_otp(userId: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        otp_code = str(random.randint(100000, 999999))
        expired_at = datetime.utcnow() + timedelta(seconds=30)
        cur.execute(
            "INSERT INTO otp (userId, otpCode, expired_at, is_used) VALUES (?, ?, ?, 0)",
            (userId, otp_code, expired_at)
        )
        conn.commit()
        logging.info(f"OTP generated for user {userId}: {otp_code}")
        return {"otpCode": otp_code, "expired_at": expired_at}
    finally:
        conn.close()

@app.post("/otp/verify")
def verify_otp(data: OTPVerifyRequest):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT otpId, expired_at, is_used FROM otp WHERE userId = ? AND otpCode = ?", (data.userId, data.otpCode))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="OTP not found")

        otp_id, expired_at, is_used = row
        if is_used:
            raise HTTPException(status_code=400, detail="OTP already used")
        if datetime.utcnow() > expired_at:
            raise HTTPException(status_code=400, detail="OTP expired")

        cur.execute("UPDATE otp SET is_used = 1 WHERE otpId = ?", (otp_id,))
        conn.commit()
        logging.info(f"OTP verified successfully for user {data.userId}")
        return {"message": "OTP verified successfully"}
    finally:
        conn.close()

# ================== Run ==================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8004)
