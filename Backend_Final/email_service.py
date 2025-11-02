from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from send_email import send_email_v1, send_bulk_email, get_email_logs
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

# ===== Cấu hình JWT =====
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

OTP_SERVICE_URL = "http://127.0.0.1:8004/otp/generate"
CUSTOMER_SERVICE_URL = "http://127.0.0.1:8000/customers"

app = FastAPI()
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

class EmailConfirmationRequest(BaseModel):
    customerId: str
    
# Dữ liệu đầu vào cho request gửi email
class EmailRequest(BaseModel):
    toList: list[str]   # Danh sách email người nhận
    subject: str        # Tiêu đề email
    body: str           # Nội dung email

# Kết quả trả về khi gửi 1 email
class EmailSingleResponse(BaseModel):
    success: bool
    message: Optional[str] = None  # Thông điệp kết quả

# Kết quả trả về khi gửi nhiều email
class EmailBulkResponse(BaseModel):
    success: bool
    sentCount: int       # Số lượng gửi thành công
    failed: List[str]    # Danh sách email bị lỗi

# Log email đã gửi 
class EmailLog(BaseModel):
    to: str
    subject: str
    status: str
    time: datetime

# Gọi Customer Service để lấy email
def get_customer_email(customer_id: str, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}

    try:
        res = requests.get(f"{CUSTOMER_SERVICE_URL}/{customer_id}", headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("email")
        elif res.status_code == 404:
            raise HTTPException(status_code=404, detail="Customer not found in Customer Service")
        else:
            raise HTTPException(status_code=502, detail="Customer Service error")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Customer Service unavailable: {e}")

@app.post("/email/send-confirmation", response_model=EmailSingleResponse, status_code=status.HTTP_200_OK)
def send_confirmation_email(request: EmailConfirmationRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Lấy email từ Customer Service
        recipient_email = get_customer_email(request.customerId, token)
        
        # Gọi OTP Service
        res = requests.post(OTP_SERVICE_URL, params={"userId": request.customerId}, headers=headers, timeout=5)
        if res.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to generate OTP from OTP Service")

        otp_code = res.json().get("otpCode")

        subject = "Payment Confirmation Email - Elevate iBanking"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px; color: #333;">
            <div style="max-width: 600px; margin: auto; background: #fff;
                        padding: 20px; border-radius: 10px; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

            <!-- Header -->
            <h2 style="color: #2E86C1; text-align: center; margin-bottom: 20px;">
                Elevate iBanking - Payment Confirmation
            </h2>

            <!-- Greeting -->
            <p style="font-size: 16px;">Dear <b>Customer</b>,</p>

            <!-- Message -->
            <p style="font-size: 15px; line-height: 1.6;">
                This is a confirmation email from <b>Elevate iBanking</b>.
                Please use the OTP code below to enter in the web application:
            </p>

            <!-- OTP Box -->
            <div style="text-align: center; margin: 20px 0;">
                <span style="display: inline-block; 
                            padding: 12px 20px; 
                            font-size: 22px; 
                            font-weight: bold; 
                            color: #fff; 
                            background: #E74C3C; 
                            border-radius: 8px;">
                {otp_code}
                </span>
            </div>

            <!-- Note -->
            <p style="font-size: 14px; color: #D35400;">
                <b>Note:</b> This OTP will expire in <b>2 minutes</b>.
            </p>

            <!-- Footer -->
            <p style="margin-top: 30px; font-size: 14px;">
                Thank you for using our service.  
                <br>
                — <b>Elevate iBanking Team</b>
            </p>
            <hr style="margin: 20px 0;">
            <footer style="font-size: 12px; text-align: center; color: #999;">
                © 2025 Elevate iBanking - All rights reserved
            </footer>
            </div>
        </body>
        </html>
        """

        # Gửi email
        ok = send_email_v1(recipient_email, subject, body, html=True)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to send confirmation email")

        return {"success": True, "message": f"Confirmation email sent to {recipient_email}"}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"OTP Service unavailable: {e}")
    
# Dùng cho việc gửi mail update balance bên account service
@app.post("/email/send", response_model=EmailSingleResponse,status_code=status.HTTP_200_OK)
def send_single_email(request: EmailRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)

    if len(request.toList) != 1:
        # Nếu gửi nhiều hơn 1 người → lỗi 400 (Bad Request)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only 1 recipient allowed"
        )
    ok = send_email_v1(request.toList[0], request.subject, request.body,html=True)
    if not ok:
        # Nếu gửi thất bại → lỗi 500 (Internal Server Error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email could not be sent, please try again."
        )
    return {"success": True, "message": "Email sent successfully."}

@app.post("/email/send-bulk", response_model=EmailBulkResponse,status_code=status.HTTP_200_OK)
def send_bulk(request: EmailRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)

    if len(request.toList) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The recipient list (toList) cannot be empty."
        )
    count, failed = send_bulk_email(request.toList, request.subject, request.body)
    return {"success": True, "sentCount": count, "failed": failed}


@app.get("/email/logs", response_model=List[EmailLog],status_code=status.HTTP_200_OK)
def get_logs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)

    return get_email_logs()
