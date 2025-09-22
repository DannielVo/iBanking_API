from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
import random, redis

from otp_service import schemas

router = APIRouter(
    prefix="/otp",
    tags=["otp"]
)

# Kết nối Redis (DB số 2 dành riêng cho OTP)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# ----------------- GENERATE OTP -----------------
@router.post("/generate")
async def generate_otp(request: schemas.OTPRequest):
    otp_code = str(random.randint(100000, 999999))  # OTP gồm 6 số

    # Key cho Redis: otp:user_id
    key = f"otp:{request.userId}"

    # Lưu OTP với TTL = 30s
    redis_client.setex(key, 30, otp_code)

    return {
        "message": "OTP generated",
        "otp": otp_code,   # Chỉ trả về để test, thực tế gửi SMS/Email
        "expiry_seconds": 30
    }


# ----------------- VERIFY OTP -----------------
@router.post("/verify")
async def verify_otp(request: schemas.VerifyOTPRequest):
    key = f"otp:{request.user_id}"
    stored_otp = redis_client.get(key)

    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP expired or not found")

    if stored_otp != request.code:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Nếu OTP đúng → xóa để tránh dùng lại
    redis_client.delete(key)

    return {"message": "OTP valid", "user_id": request.user_id}
