from fastapi import FastAPI, status, Depends, HTTPException
import redis, random, hashlib, time
from datetime import datetime, timedelta, timezone
import models
from database import engine, SessionLocal
from typing import Annotated, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import auth
import uuid, json
from auth import get_current_user
from pydantic import BaseModel

# -------------------- INIT --------------------
app = FastAPI()
app.include_router(auth.router)

models.Base.metadata.create_all(bind=engine)

# Redis client
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


# -------------------- DEPENDENCIES --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# -------------------- MODELS --------------------
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

class OTPRequest(BaseModel):
    userId: int  

class OTPVerify(BaseModel):
    userId: int
    otp: str


# -------------------- UTILS --------------------
def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


# -------------------- ROOT --------------------
@app.get("/", status_code=status.HTTP_200_OK)
async def user(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='Authentication Failed')
    return {"User": user}


# -------------------- ACCOUNTS --------------------
@app.get("/accounts/by-customer/{customer_id}")
def get_accounts_by_customer(customer_id: int, db: Session = Depends(get_db)):
    accounts = db.query(models.Account).filter(models.Account.customerId == customer_id).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found for this customer")
    return accounts        


# -------------------- SAFE PAYMENT --------------------
@app.post("/payments/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payment: PaymentRequest, db: db_dependency):
    try:
        account = (
            db.execute(
                select(models.Account)
                .where(models.Account.accountId == payment.accountId)
                .with_for_update()
            )
            .scalars()
            .first()
        )

        if not account: 
            raise HTTPException(status_code=404, detail="Account not found")
        
        if account.balance < payment.amount:
            status_payment = "failed"
            history = {"event": "Payment failed", "reason": "Insufficient balance"}
        else:
            account.balance -= payment.amount
            status_payment = "success"
            history = {"event": "Payment success", "remaining_balance": account.balance}
            
        new_payment = models.Payment(
            transactionId=str(uuid.uuid4()), 
            accountId=payment.accountId,
            amount=payment.amount,
            payment_status=status_payment,
            transaction_history=json.dumps([history])
        )
        
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        return new_payment
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# -------------------- GET PAYMENTS --------------------
@app.get("/payments/{account_id}", response_model = List[PaymentResponse])
async def get_payments(account_id: int, db: db_dependency):
    payments = db.query(models.Payment).filter(models.Payment.accountId == account_id).all()
    if not payments:
        raise HTTPException(status_code=404, detail = "No payments found")
    return payments

@app.get("/payments/transaction/{transaction_id}", response_model=PaymentResponse)
async def get_payment(transaction_id: str, db: db_dependency):
    payment = db.query(models.Payment).filter(models.Payment.transactionId == transaction_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


# -------------------- OTP --------------------
@app.post("/otp/request")
def request_otp(data: OTPRequest, db: Session = Depends(get_db)):
    user = db.query(models.Authentication).filter(models.Authentication.userid == data.userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Chặn spam OTP (30s)
    last_sent_key = f"otp:sent:{data.userId}"
    if redis_client.get(last_sent_key):
        raise HTTPException(status_code=429, detail="Wait 30s before requesting a new OTP")

    # Tạo OTP 6 số
    otp = f"{random.randint(0, 999999):06d}"
    otp_hash = hash_otp(otp)
    expire_time = datetime.now(timezone.utc) + timedelta(seconds=60)

    # Lưu OTP raw vào Redis (để verify)
    redis_client.setex(f"otp:{data.userId}", 60, otp)
    redis_client.setex(last_sent_key, 30, "1")

    # Lưu log OTP hashed vào DB
    new_otp = models.OTP(
        userId=data.userId,
        otpCode=otp_hash,
        expired_at=expire_time,
        is_used=False
    )
    db.add(new_otp)
    db.commit()
    db.refresh(new_otp)

    return {"message": "OTP sent", "otp_demo": otp}  # ⚠️ chỉ để debug


@app.post("/otp/verify")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    otp_stored = redis_client.get(f"otp:{data.userId}")
    if not otp_stored:
        raise HTTPException(status_code=400, detail="OTP expired or not found")

    if data.otp != otp_stored:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    otp_entry = db.query(models.OTP).filter(
        models.OTP.userId == data.userId,
        models.OTP.is_used == False
    ).order_by(models.OTP.expired_at.desc()).first()

    if not otp_entry:
        raise HTTPException(status_code=404, detail="OTP record not found in DB")

    # So sánh timezone-aware datetime
    if otp_entry.expired_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")

    # Đánh dấu đã dùng
    otp_entry.is_used = True
    db.commit()

    # Xóa OTP trong Redis sau khi verify thành công
    redis_client.delete(f"otp:{data.userId}")

    return {"message": "OTP verified successfully"}
