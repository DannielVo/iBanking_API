from fastapi import FastAPI,HTTPException, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import logging
import pyodbc   
import requests


app = FastAPI()

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
    description: str # có cần thiết phải có cái này không, mục đích của nó là gì
    
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-ITBGSRM\MSSQLSERVER01;" # Thay bằng tên sever trên máy đang chạy
        "DATABASE=AccountDB;"
        "Trusted_Connection=yes;"
    )    

CUSTOMER_SERVICE_URL = "http://127.0.0.1:8000/customers" # Lấy URL gốc của customer_service

# Xử lý lỗi hệ thống (500) toàn cục
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")  # log lỗi để debug
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please try again later."},
    )  
    
@app.get("/account/{customer_id}",response_model=list[Account])
def getAccountinfo(customer_id : str):
    res = requests.get(f"{CUSTOMER_SERVICE_URL}/{customer_id}",timeout=5)
    connct = get_connection()
    cur = connct.cursor()
    cur.execute("SELECT customer_id, account_id, balance FROM account WHERE customer_id = ?", customer_id)
    row = cur.fetchall() 
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
      
      
@app.put("/account/updateBalance",response_model=AccountResponse)
def update_balance(data: BalanceUpdate):
    # Lấy account theo account_id từ DB
    account = find_account_by_id(data.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    # Tính số dư mới
    new_balance = account.balance + data.amount
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
    
    return AccountResponse(
    customer_id=account.customer_id,
    account_id=account.account_id,
    balance=new_balance,
    status="Success"
)

    
    