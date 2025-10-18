import os.path
import base64
import pyodbc

from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from typing import List

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-PV9Q0OQ\SQLEXPRESS;" # Thay bằng tên sever trên máy đang chạy
        "DATABASE=EmailDB;"   
        "Trusted_Connection=yes;"
    )
        
def log_email(recipient, subject, status, error_message=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO EmailLogs (recipient, subject, status, error_message, sent_time) VALUES (?, ?, ?, ?, GETDATE())",
            (recipient, subject, status, error_message)
        )
        conn.commit()
    finally:
        conn.close()


def send_email_v1(recipient: str, subject: str, content: str, port: int = 0, html: bool = False) -> bool:
    """Send email using Gmail API"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials_desktop_apps.json', SCOPES)
            creds = flow.run_local_server(port=port)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)

        # Tạo email
        message = EmailMessage()
        message['Subject'] = subject 
        message.set_content(content)
        message['To'] = recipient
        message['From'] = formataddr(('iBanking App', service.users().getProfile(userId='me').execute()['emailAddress']))

        if html:
            message.add_alternative(content, subtype="html")
        else:
            message.set_content(content)
            
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        service.users().messages().send(userId="me", body=create_message).execute()
        # Lưu log khi thành công
        log_email(recipient, subject, "success")
        return True
    except HttpError as e:
        # Lưu log khi thất bại
        log_email(recipient, subject, "failed", str(e))
        print(f'Error occurred: {e}')
        return False
    
    
def send_bulk_email(to_list: List[str], subject: str, body: str):
    success_count, failed = 0, []
    for recipient in to_list:
        if send_email_v1(recipient, subject, body,html= True):
            success_count += 1
        else:
            failed.append(recipient)
    return success_count, failed

def get_email_logs():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT recipient, subject, status, sent_time FROM EmailLogs ORDER BY sent_time DESC")
        rows = cur.fetchall()
        return [
            {
                "to": row[0],
                "subject": row[1],
                "status": row[2],
                "time": row[3]
            }
            for row in rows
        ]
    finally:
        conn.close()
