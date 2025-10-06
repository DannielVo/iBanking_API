from fastapi import FastAPI,HTTPException, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import logging
import pyodbc   
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

# Cấu hình logging để theo dõi lỗi
logging.basicConfig(level=logging.ERROR)

class Account(BaseModel):
    customer_id : str
    account_id: str
    balance : float 

class AccountResponse(Account):   # kế thừa từ Account
    status: str

#định nghĩa lớp tham số đầu vô 
class BalanceUpdate(BaseModel):
    account_id: str
    amount: float
    description: str 
    
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-PV9Q0OQ\SQLEXPRESS;" # Thay bằng tên sever trên máy đang chạy
        "DATABASE=AccountDB;"
        "Trusted_Connection=yes;"
    )    
    
# Lấy URL gốc của customer_service
CUSTOMER_SERVICE_URL = "http://127.0.0.1:8000/customers" 
# Email Service URL
EMAIL_SERVICE_URL = "http://127.0.0.1:8005/email/send"

# Xử lý lỗi hệ thống (500) toàn cục
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")  # log lỗi để debug
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please try again later."},
    )  
    
@app.get("/account/{customer_id}",response_model=Account)
def getAccountinfo(customer_id : str):
    res = requests.get(f"{CUSTOMER_SERVICE_URL}/{customer_id}",timeout=5)
    connct = get_connection()
    cur = connct.cursor()
    cur.execute("SELECT customer_id, account_id, balance FROM account WHERE customer_id = ?", customer_id)
    row = cur.fetchone() 
    try:
        # Trả về thành công
        if res.status_code == 200:
            return row
        
        # Không tìm thấy
        if res.status_code == 404:
            raise HTTPException(status_code=404,detail="Customer not found")
        
        # Bị cấm hoặc lỗi nghiệp vụ khác
        elif res.status_code == 403:
            raise HTTPException(status_code=403, detail="Customer is inactive or forbidden")
        
        # Lỗi khác 
        else:
            raise HTTPException(status_code=502, detail="Customer Service error")
    
    except requests.exceptions.RequestException as e:
        # Lỗi khi không kết nối được sang Customer Service (mất mạng, timeout, service chết)
        raise HTTPException(status_code=503, detail="Customer Service unavailable")
    finally:
        if connct:
            connct.close()

def find_account_by_id(account_id: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT customer_id, account_id, balance FROM account WHERE account_id = ?",
            account_id
        )
        row = cur.fetchone()
        if not row:
            return None
        return Account(                    
            customer_id = row[0],
            account_id = row[1],
            balance = float(row[2]),
        )
    finally:
        conn.close()

# Lấy email khách hàng từ Customer Service
def get_customer_email(customer_id: str) -> str:
    try:
        res = requests.get(f"{CUSTOMER_SERVICE_URL}/{customer_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("email")
        elif res.status_code == 404:
            raise HTTPException(status_code=404, detail="Customer not found in Customer Service")
        else:
            raise HTTPException(status_code=502, detail="Customer Service error")
    except requests.exceptions.RequestException as e:
        logging.error(f"Customer Service unavailable: {e}")
        raise HTTPException(status_code=503, detail="Customer Service unavailable")
    
# Lấy tên khách hàng
def get_customer_name(customer_id: str) -> str:
    try:
        res = requests.get(f"{CUSTOMER_SERVICE_URL}/{customer_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("full_name")
        elif res.status_code == 404:
            raise HTTPException(status_code=404, detail="Customer not found in Customer Service")
        else:
            raise HTTPException(status_code=502, detail="Customer Service error")
    except requests.exceptions.RequestException as e:
        logging.error(f"Customer Service unavailable: {e}")
        raise HTTPException(status_code=503, detail="Customer Service unavailable")

# Hàm gửi email bằng cách gọi sang Email Service
def notify_email(recipient: str, subject: str, body: str):
    payload = {
        "toList": [recipient],
        "subject": subject,
        "body": body
    }
    try:
        res = requests.post(EMAIL_SERVICE_URL, json=payload, timeout=5)
        if res.status_code != 200:
            logging.error(f"Email service returned {res.status_code}: {res.text}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to connect to Email Service: {e}")
        return False      
    
@app.put("/account/updateBalance",response_model=AccountResponse)
def update_balance(data: BalanceUpdate):
    # Lấy account theo account_id từ DB
    account = find_account_by_id(data.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    # Tính số dư mới
    new_balance = account.balance - data.amount
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Chặn amount = 0
    if data.amount == 0:
        raise HTTPException(status_code=400, detail="Amount must be non-zero")

    # Cập nhật DB trong transaction
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE account SET balance = ? WHERE account_id = ?",
            (new_balance, data.account_id)
        )
        conn.commit()
    except pyodbc.Error as e:
        logging.error(f"DB error in update_balance: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()
    
    # Lấy email khách hàng từ Customer Service
    customer_email = get_customer_email(account.customer_id)
    customer_name = get_customer_name(account.customer_id)
    # Gọi Email Service để gửi thông báo
    subject = "Account Balance Updated"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #f8f9fa; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">
        <h2 style="color: #2E86C1; text-align:center;">Elevate iBanking - Account Balance Update</h2>
        <p>Dear <b>{customer_name}</b>,</p>
        <p>Your account <b>{account.account_id}</b> has been updated successfully.</p>
        <p>
            <b>New Balance:</b> <span style="color:green;">{new_balance:,.2f} VND</span><br>
            <b>Description:</b> {data.description}
        </p>
        <p style="margin-top:20px;">Thank you for using <b>Elevate iBanking</b>.</p>
        <hr>
        <footer style="font-size:12px; text-align:center; color:#999;">
            © 2025 Elevate iBanking - All rights reserved
        </footer>
        </div>
    </body>
    </html>
    """
    # Muốn test thì thay customer_email thành gmail của mình
    notify_email(customer_email, subject, body)
    
    return AccountResponse(
    customer_id=account.customer_id,
    account_id=account.account_id,
    balance=new_balance,
    status="Success"
)

    
    