from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from send_email import send_email_v1, send_bulk_email, get_email_logs
import requests

OTP_SERVICE_URL = "http://127.0.0.1:8004/otp/generate"
CUSTOMER_SERVICE_URL = "http://127.0.0.1:8000/customers"

app = FastAPI()

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
        raise HTTPException(status_code=503, detail=f"Customer Service unavailable: {e}")

@app.post("/email/send-confirmation", response_model=EmailSingleResponse, status_code=status.HTTP_200_OK)
def send_confirmation_email(request: EmailConfirmationRequest):
    try:
        # Lấy email từ Customer Service
        recipient_email = get_customer_email(request.customerId)
        
        # Gọi OTP Service
        res = requests.post(OTP_SERVICE_URL, params={"userId": request.customerId}, timeout=5)
        if res.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to generate OTP from OTP Service")

        otp_code = res.json().get("otpCode")

        subject = "Payment Confirmation Email - Elevate iBanking"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color:#2E86C1;">Elevate iBanking - Payment Confirmation</h2>
            <p>Dear Customer,</p>
            <p>This is a confirmation email from <b>Elevate iBanking</b>.</p>
            <p>Please use the OTP code below to enter in the web application:</p>
            <h3 style="color:#E74C3C; font-size: 24px;">🔑 {otp_code}</h3>
            <p style="color:#D35400;"><b>⚠️ Note:</b> This OTP will expire in 2 minutes.</p>
            <br>
            <p>Thank you for using our service.</p>
            <hr>
            <footer style="font-size:12px; color:#888;">
              © 2025 Elevate iBanking - All rights reserved
            </footer>
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
def send_single_email(request: EmailRequest):
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
def send_bulk(request: EmailRequest):
    if len(request.toList) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The recipient list (toList) cannot be empty."
        )
    count, failed = send_bulk_email(request.toList, request.subject, request.body)
    return {"success": True, "sentCount": count, "failed": failed}


@app.get("/email/logs", response_model=List[EmailLog],status_code=status.HTTP_200_OK)
def get_logs():
    return get_email_logs()
