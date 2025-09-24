from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from send_email import send_email_v1, send_bulk_email, get_email_logs

app = FastAPI()

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

# Log email đã gửi (chỉ demo, thực tế nên lưu DB)
class EmailLog(BaseModel):
    to: str
    subject: str
    status: str
    time: datetime

@app.post("/email/send", response_model=EmailSingleResponse,status_code=status.HTTP_200_OK)
def send_single_email(request: EmailRequest):
    if len(request.toList) != 1:
        # Nếu gửi nhiều hơn 1 người → lỗi 400 (Bad Request)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only 1 recipient allowed"
        )
    ok = send_email_v1(request.toList[0], request.subject, request.body)
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
