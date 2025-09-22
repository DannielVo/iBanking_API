from pydantic import BaseModel


# -------- Auth --------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    user_id: int | None = None


# -------- OTP --------
class OTPRequest(BaseModel):
    userId: int


class OTPVerify(BaseModel):
    userId: int
    otp: str


# -------- Payment --------
class PaymentRequest(BaseModel):
    accountId: int
    amount: float


class PaymentResponse(BaseModel):
    transactionId: str
    accountId: int
    amount: float
    payment_status: str
    transaction_history: str

    class Config:
        orm_mode = True
