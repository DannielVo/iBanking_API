from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timedelta, timezone
from sqlalchemy.dialects.mssql import DATETIMEOFFSET

class Authentication(Base):
    __tablename__ = "Authentication"
    
    userid = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    otps = relationship("OTP", back_populates="user")
    
class  Account(Base):
    __tablename__ = "Account"
    
    accountId = Column(Integer, primary_key=True, index=True)
    customerId = Column(Integer, ForeignKey("Authentication.userid"))
    balance = Column(Float, default=0.0)
    
    payments = relationship("Payment", back_populates="account")
    
class Payment(Base):
    
    __tablename__ = "Payment"
    transactionId = Column(String(36), primary_key=True, autoincrement=False, index=True)
    accountId = Column(Integer, ForeignKey("Account.accountId"))
    amount = Column(Integer, nullable=False)
    payment_status = Column(String(20), default="pending")
    dueDate = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    transaction_history = Column(Text)
    
    account = relationship("Account", back_populates="payments")
    
    
class OTP(Base):
    __tablename__ = "otp"
    otpId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, ForeignKey("Authentication.userid"))
    otpCode = Column(String(64), nullable=False)
    expired_at = Column(DATETIMEOFFSET, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(seconds=60))
    is_used = Column(Boolean, default=False)
    user = relationship("Authentication", back_populates="otps")