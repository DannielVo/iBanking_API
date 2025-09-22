from pydantic import BaseModel

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
