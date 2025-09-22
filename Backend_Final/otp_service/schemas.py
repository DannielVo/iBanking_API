from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class OTPRequest(BaseModel):
    userId: int


class OTPVerify(BaseModel):
    userId: int
    otp: str


class OTPResponse(BaseModel):
    otpId: int
    userId: int
    otpCode: str
    expired_at: datetime
    is_used: bool

class VerifyOTPRequest(BaseModel):
    user_id: int
    code: str
    
class Config:
    orm_mode = True
