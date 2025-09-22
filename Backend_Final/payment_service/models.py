from sqlalchemy import Column, Integer, String, Float, Text
from .database import Base

class Payment(Base):
    __tablename__ = "Payment"

    transactionId = Column(String(36), primary_key=True, index=True)
    accountId = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    transaction_history = Column(Text)
