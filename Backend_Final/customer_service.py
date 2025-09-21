import uvicorn 
from fastapi import FastAPI,HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from fastapi.responses import JSONResponse
from typing import Annotated
import logging
import pyodbc



app = FastAPI()

# Cấu hình logging để theo dõi lỗi
logging.basicConfig(level=logging.ERROR)

class Customer(BaseModel):
    customer_id : str
    full_name: str
    phone_number: Annotated[str, Field(pattern=r"^(0\d{9})$")]# Bắt đầu bằng 0 + 9 số = 10 số
    email: EmailStr 
    tuition_debt: float = 0.0 # Học phí cần phải đóng
    
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER= DESKTOP-ITBGSRM\MSSQLSERVER01;"       # Thay bằng tên sever trên máy đang chạy
        "DATABASE=CustomerDB;"
        "Trusted_Connection=yes;"
    )    
    
    
# Xử lý lỗi hệ thống (500) toàn cục
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")  # log lỗi để debug
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please try again later."},
    )    
     
   
@app.get("/customers/{customer_id}",response_model=Customer)
def getCustomerInfo(customer_id : str): 
    connct = get_connection()
    cur = connct.cursor()
    cur.execute("SELECT customer_id, full_name, phone_number, email , tuition_debt FROM Customers WHERE customer_id = ?", customer_id)
    row = cur.fetchone()
    try:
        # Trường hợp 404
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Trường hợp 200
        return row

    except HTTPException as http_exc:
        # Các lỗi có chủ ý (404, 403) vẫn trả như bình thường
        raise http_exc
    except Exception as e:
        # Các lỗi khác -> 500
        logging.error(f"Unexpected error in get_customer: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    finally:
        if connct:
            connct.close()

@app.get("/customers/tuition/{customer_id}")
def getTuition(customer_id:str):
    connct = get_connection()
    try:
        cur = connct.cursor()
        cur.execute("SELECT tuition_debt FROM Customers WHERE customer_id = ?", customer_id)
        row = cur.fetchone()            
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"customer_id": customer_id, "tuition_debt": row[0]}
    
    except HTTPException as http_exc:
        # Các lỗi có chủ ý (404, 403) vẫn trả như bình thường
        raise http_exc
    except Exception as e:
        # Các lỗi khác -> 500
        logging.error(f"Unexpected error in get_customer: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    finally:
        connct.close()
        