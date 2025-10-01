from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import pyodbc
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Payment Service")

# Cho phép origin từ React
origins = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",   
    # có thể thêm domain production sau này
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # danh sách origin được phép
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, PUT, DELETE...
    allow_headers=["*"],          # cho phép mọi header
)

# ================== Logging ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ================== DB Connection ==================
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-PV9Q0OQ\SQLEXPRESS;"
        "DATABASE=PaymentDB;"
        "Trusted_Connection=yes;"
    )

# ================== Models ==================
class CreatePaymentRequest(BaseModel):
    customerId: int
    amount: float
    description: str

class MakePaymentRequest(BaseModel):
    accountId: str
    customerId: str

# URL tới Account Service (cần implement bên account_service)
ACCOUNT_SERVICE_URL = "http://127.0.0.1:8001/account"

# ================== Exception Handler ==================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error. Please try again later."})

# ================== Create Payment ==================
@app.post("/payment/create")
def create_payment(data: CreatePaymentRequest):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO payment (customerId, amount, status, transaction_history)
            VALUES (?, ?, ?, ?)
            """,
            (data.customerId, data.amount, "unpaid", data.description)
        )
        conn.commit()
        logging.info(f"Created new payment for customer {data.customerId}")
        return {"message": "Payment created successfully"}
    except Exception as e:
        conn.rollback()
        logging.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail="Error creating payment")
    finally:
        conn.close()

# ================== Find Unpaid Payment ==================
@app.get("/payment/unpaid/{customerId}")
def find_unpaid_payment(customerId: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT TOP 1 transactionId, amount, status FROM payment WHERE customerId = ? AND status = 'unpaid'",
            (customerId,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No unpaid payment found")
        return {"transactionId": row[0], "amount": row[1], "status": row[2]}
    except HTTPException:  # để nguyên 404 cho FastAPI xử lý
        raise
    except Exception as e:
        logging.error(f"Error finding unpaid payment: {e}")
        raise HTTPException(status_code=500, detail="Error finding unpaid payment")
    finally:
        conn.close()

# ================== Make Payment ==================
@app.post("/payment/make")
def make_payment(data: MakePaymentRequest):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Lấy unpaid payment
        cur.execute(
            "SELECT TOP 1 transactionId, amount FROM payment WHERE customerId = ? AND status = 'unpaid'",
            (data.customerId,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No unpaid payment found")

        transactionId, amount = row
        logging.info("Thanh cong buoc lay unpaid payment")

        # Gọi sang Account Service để lấy balance
        try:
            res = requests.get(f"{ACCOUNT_SERVICE_URL}/{data.customerId}", timeout=5)
            if res.status_code != 200:
                raise HTTPException(status_code=404, detail="Account not found")
            account = res.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Cannot connect to Account Service: {e}")
            raise HTTPException(status_code=503, detail="Account Service unavailable")

        logging.info("Thanh cong buoc lay Account info")

        logging.info(f"Account: {account}")
        balance = float(account["balance"])
        # balance = account["balance"]

        logging.info(f"Balance: {balance}")
        logging.info(f"Amount: {amount}")

        if balance < amount:
            logging.warning(f"Customer {data.customerId} insufficient funds. Balance: {balance}, Need: {amount}")
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        logging.info("Thanh cong buoc lay balance va so sanh balance")


        # Gọi API update_balance bên Account Service
        try:
            update_res = requests.put(
                f"{ACCOUNT_SERVICE_URL}/updateBalance",
                json={"account_id": data.accountId, "amount": float(amount), "description": ""},
                timeout=5
            )
            if update_res.status_code != 200:
                # raise HTTPException(status_code=400, detail="Balance update failed")
                raise HTTPException(status_code=400, detail=update_res.detail)
        except requests.exceptions.RequestException as e:
            logging.error(f"Update balance API error: {e}")
            raise HTTPException(status_code=503, detail="Account Service unavailable during balance update")
        
        logging.info("Thanh cong buoc update balance")


        # Update status payment → paid
        cur.execute(
            "UPDATE payment SET status = 'paid', transaction_history = ? WHERE transactionId = ?",
            (f"Paid {amount}", transactionId)
        )
        conn.commit()

        logging.info("Thanh cong buoc update status")


        logging.info(f"Payment {transactionId} for customer {data.customerId} marked as PAID")
        return {"message": "Payment successful", "transactionId": transactionId, "status": "paid"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logging.error(f"Payment processing failed: {e}")
        raise HTTPException(status_code=500, detail="Payment transaction failed")
    finally:
        conn.close()

# ================== Run ==================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
