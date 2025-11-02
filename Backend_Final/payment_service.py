from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import pyodbc
import requests
import json
import decimal
import threading
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

# ===== Cấu hình JWT =====
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Payment Service")
security = HTTPBearer()

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

# ===== Giải mã và xác thực token =====
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

# ================== Models ==================
class CreatePaymentRequest(BaseModel):
    customerId: int
    amount: float
    description: str

class MakePaymentRequest(BaseModel):
    customerId: str
    customerPaymentId: str
    accountId: str

# ================== Global Lock Dictionary ==================
# Dùng để đảm bảo không 2 giao dịch cùng lúc trên cùng 1 tài khoản
account_locks = {}
account_locks_lock = threading.Lock()  # khóa bảo vệ dictionary

def get_lock_for_customer(customer_id: int):
    """Tạo và trả về khóa riêng cho từng customerId, đảm bảo thread-safe"""
    with account_locks_lock:
        if customer_id not in account_locks:
            account_locks[customer_id] = threading.Lock()
        return account_locks[customer_id]

# ================== Decimal Helper ==================
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

# ================== URL tới Account Service ==================
ACCOUNT_SERVICE_URL = "http://127.0.0.1:8001/account"

# ================== Exception Handler ==================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error. Please try again later."})

# ================== Create Payment ==================
@app.post("/payment/create")
def create_payment(data: CreatePaymentRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)

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

# ================== Find Paid Payment ==================
@app.get("/payment/paid/{customerId}")
def find_paid_payment(customerId: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)

    conn = get_connection()
    cur = conn.cursor()
    try:
        logging.info("Vua vao ham paid")
        cur.execute(
            "SELECT transactionId, amount, status, customerId, semester, description, datePayment FROM payment WHERE customerPayId = ? AND status = 'paid'",
            (customerId,)
        )
        rows = cur.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No paid payments found")

        logging.info(f"Da tim duoc {len(rows)} dong du lieu")

        payments = [
            {
                "transactionId": row[0],
                "amount": float(row[1]),
                "status": row[2],
                "customerId": row[3],
                "semester": row[4],
                "description": row[5],
                "datePayment": row[6],
            }
            for row in rows
        ]

        logging.info(f"Ket qua payment la: {payments}")

        semesters = sorted({p["semester"] for p in payments})

        logging.info(f"Semesters tim duoc: {semesters}")

        response = {
                "semesters": semesters,
                "payments": payments
        }        

        # Trả về list JSON hợp lệ
        return JSONResponse(content=jsonable_encoder(response))

    except HTTPException as http_exc:
        # Các lỗi có chủ ý (404, 403) vẫn trả như bình thường
        raise http_exc
    
    except Exception as e:
        logging.error(f"Error finding paid payment: {e}")
        raise HTTPException(status_code=500, detail="Error finding paid payment")
    finally:
        conn.close()


# ================== Find Unpaid Payment ==================
@app.get("/payment/unpaid/{customerId}")
def find_unpaid_payment(customerId: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT TOP 1 transactionId, amount, status, semester, description FROM payment WHERE customerId = ? AND status = 'unpaid'",
            (customerId,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No unpaid payment found")

        result = {"transactionId": row[0], "amount": float(row[1]), "status": row[2], "semester": row[3], "description": row[4],}
        return JSONResponse(content=json.loads(json.dumps(result, default=decimal_default)))
    
    except HTTPException as http_exc:
        # Các lỗi có chủ ý (404, 403) vẫn trả như bình thường
        raise http_exc
    
    except Exception as e:
        logging.error(f"Error finding unpaid payment: {e}")
        raise HTTPException(status_code=500, detail="Error finding unpaid payment")
    finally:
        conn.close()

# ================== Make Payment ==================
@app.post("/payment/make")
def make_payment(data: MakePaymentRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    headers = {"Authorization": f"Bearer {token}"}
    
    lock = get_lock_for_customer(data.customerId)

    logging.info("Da qua buoc get customer lock")

    # Thử acquire lock để ngăn giao dịch song song cùng tài khoản
    if not lock.acquire(blocking=False):
        logging.warning(f"Concurrent transaction detected for customer {data.customerId}.")
        raise HTTPException(status_code=409, detail="Another transaction is being processed for this account. Please wait.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        logging.info("Da qua buoc get lock")
        # --- Kiểm tra unpaid payment (sau khi đã khóa tài khoản) ---
        cur.execute(
            "SELECT TOP 1 transactionId, amount FROM payment WHERE customerId = ? AND status = 'unpaid'",
            (data.customerPaymentId,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No unpaid payment found")

        transactionId, amount = row
        amount = float(amount)

        logging.info("Da qua buoc get unpaid")

        # --- Lấy thông tin tài khoản từ Account Service ---
        try:
            res = requests.get(f"{ACCOUNT_SERVICE_URL}/{data.customerId}", headers=headers, timeout=5)
            if res.status_code != 200:
                logging.error(f"Account Service error: {res.text}")
                raise HTTPException(status_code=404, detail="Account not found")
            account_data = res.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Cannot connect to Account Service: {e}")
            raise HTTPException(status_code=503, detail="Account Service unavailable")

        if isinstance(account_data, list) and len(account_data) > 0:
            account = account_data[0]
        elif isinstance(account_data, dict):
            account = account_data
        else:
            raise HTTPException(status_code=500, detail="Invalid account data format")
        
        logging.info("Da qua buoc get account")

        # balance = float(account.get("balance", 0))
        balance = float(account["balance"])

        logging.info("Da qua buoc get balance")

        if balance < amount:
            logging.warning(f"Customer {data.customerId} insufficient funds. Balance: {balance}, Need: {amount}")
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        logging.info(f"Balance: {balance}")
        logging.info(f"Amount: {amount}")
        logging.info(f"Balance - Amount: {balance - amount}")

        # --- Cập nhật số dư bên Account Service ---
        update_payload = {"account_id": data.accountId, "amount": amount, "description": ""}
        try:
            update_res = requests.put(
                f"{ACCOUNT_SERVICE_URL}/update-balance",
                json=update_payload,
                headers=headers,
                timeout=5
            )
            if update_res.status_code != 200:
                raise HTTPException(status_code=400, detail="Balance update failed")
        except requests.exceptions.RequestException as e:
            logging.error(f"Update balance API error: {e}")
            raise HTTPException(status_code=503, detail="Account Service unavailable during balance update")
        
        logging.info("Da qua buoc update balance")

        datePayment = datetime.utcnow() + timedelta(seconds=120)

        # --- Đánh dấu thanh toán hoàn tất ---
        cur.execute(
            "UPDATE payment SET status = 'paid', transaction_history = ?, customerPayId = ?, datePayment = ? WHERE transactionId = ?",
            (f"Paid {amount}", data.customerId, datePayment, transactionId)
        )
        conn.commit()

        logging.info("Da qua buoc update payment")

        result = {
            "message": "Payment successful",
            "transactionId": transactionId,
            "amount": amount,
            "status": "paid"
        }

        return JSONResponse(content=json.loads(json.dumps(result, default=decimal_default)))

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logging.error(f"Payment processing failed: {e}")
        raise HTTPException(status_code=500, detail="Payment transaction failed")
    finally:
        lock.release()
        conn.close()

# ================== Run ==================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
