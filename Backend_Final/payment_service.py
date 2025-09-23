from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import pyodbc
import requests

app = FastAPI(title="Payment Service")

# ================== Logging ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ================== DB Connection ==================
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=ADIDAPHAT\\MSSQLSERVER01;"
        "DATABASE=PaymentDB;"
        "Trusted_Connection=yes;"
    )

# ================== Models ==================
class PaymentRequest(BaseModel):
    accountId: str
    amount: float   # số tiền cần nộp
    description: str

# URL tới Account Service
ACCOUNT_SERVICE_URL = "http://127.0.0.1:8002/account_service"

# ================== Exception Handler ==================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error. Please try again later."})

# ================== Payment Logic ==================
@app.post("/payment/transaction")
def make_payment(data: PaymentRequest):
    # Step 1: Lấy thông tin account từ Account Service
    try:
        res = requests.get(f"{ACCOUNT_SERVICE_URL}/{data.accountId}", timeout=5)
        if res.status_code != 200:
            raise HTTPException(status_code=404, detail="Account not found")
        account = res.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Cannot connect to Account Service: {e}")
        raise HTTPException(status_code=503, detail="Account Service unavailable")

    balance = float(account["balance"])

    # Step 2: Check balance
    if balance < data.amount:
        logging.warning(f"Payment failed - insufficient funds on account {data.accountId}")
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Step 3: Thực hiện transaction trong DB với isolation
    conn = get_connection()
    try:
        conn.autocommit = False  # đảm bảo transaction atomic
        cur = conn.cursor()

        # Lock row để tránh concurrent update (chống conflict)
        cur.execute("SELECT balance FROM account WITH (UPDLOCK, ROWLOCK) WHERE account_id = ?", data.accountId)
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found during lock")

        current_balance = float(row[0])
        if current_balance < data.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds (double check)")

        # Update balance
        new_balance = current_balance - data.amount
        cur.execute("UPDATE account SET balance = ? WHERE account_id = ?", (new_balance, data.accountId))

        # Insert transaction log
        cur.execute(
            "INSERT INTO payment (accountId, amount, status, transaction_history) VALUES (?, ?, ?, ?)",
            (data.accountId, data.amount, "SUCCESS", data.description)
        )

        conn.commit()
        logging.info(f"Payment success for account {data.accountId}, amount {data.amount}")

        return {"message": "Payment successful", "new_balance": new_balance}
    except Exception as e:
        conn.rollback()
        logging.error(f"Payment transaction failed: {e}")
        raise HTTPException(status_code=500, detail="Payment transaction failed")
    finally:
        conn.close()


# ================== Run ==================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
