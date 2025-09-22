from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timedelta, timezone
from sqlalchemy.dialects.mssql import DATETIMEOFFSET
from .database import Base

class OTP(Base):
    __tablename__ = "OTP"

    otpId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(Integer, nullable=False)
    otpCode = Column(String(64), nullable=False)
    expired_at = Column(DATETIMEOFFSET, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(seconds=30))
    is_used = Column(Boolean, default=False)
