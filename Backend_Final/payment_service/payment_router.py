from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from . import models, schemas, database
import uuid, json

router = APIRouter(prefix="/payments", tags=["payments"])
db_dependency = Annotated[Session, Depends(database.get_db)]


@router.post("/", response_model=schemas.PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payment: schemas.PaymentRequest, db: db_dependency):
    try:
        account = (
            db.execute(
                select(models.Account).where(models.Account.accountId == payment.accountId).with_for_update()
            ).scalars().first()
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
            status=status_payment,
            transaction_history=json.dumps([history])
        )
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        return new_payment
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
