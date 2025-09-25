# iBanking API – Customer, Account & Email Services

## 📌 Introduction
This project is a **microservice-based iBanking backend** built with **FastAPI**.  
It includes 3 services:

- **Customer Service** → manage customers & tuition fees  
- **Account Service** → manage accounts & balances (deposit/withdraw)  
- **Email Service** → send notifications via Gmail API  

The system demonstrates a workflow for **online tuition payment**.

---

## ⚙️ System Requirements
- **Python**: 3.11+  
- **SQL Server** installed & running  
- **ODBC Driver**: ODBC Driver 17 for SQL Server  
- **Google Account** with Gmail API enabled  
### Required Python Libraries
- [FastAPI](https://fastapi.tiangolo.com/) — main framework for building APIs  
- [Uvicorn](https://www.uvicorn.org/) — ASGI server to run FastAPI  
- [Pydantic](https://docs.pydantic.dev/) — data validation (BaseModel, EmailStr, Field)  
- [Requests](https://docs.python-requests.org/) — HTTP client, used in Account Service to call Customer Service  
- [PyODBC](https://github.com/mkleehammer/pyodbc) — SQL Server connector  
- [Google API Client](https://github.com/googleapis/google-api-python-client) — Gmail API integration  

You can install all dependencies via:
```bash
pip install -r requirements.txt
```

---

## 🚀 Installation Guide

1. **Clone the repository**
   ```bash
   git clone <repo-link>
   cd iBanking_API/Customer_Account_Email
   ```

2. **Configure Database Connections**  
   Each service has a `get_connection()` function that defines the SQL Server connection string.  
   Example (in `account_service.py`):
   ```python
   def get_connection():
       return pyodbc.connect(
           "DRIVER={ODBC Driver 17 for SQL Server};"
           "SERVER=DESKTOP-ITBGSRM\\MSSQLSERVER01;"  # Replace with your actual SQL Server name
           "DATABASE=AccountDB;" # Name of database
           "Trusted_Connection=yes;"
       )
   ```

   🔹 **Important**:  
   - Replace `DESKTOP-ITBGSRM\\MSSQLSERVER01` with your actual SQL Server instance name.  
   - To find your SQL Server name:  
     1. Open **SQL Server Management Studio (SSMS)**.  
     2. In the login window, check the "Server name" field.  
        Examples:  
        - `.\SQLEXPRESS`  
        - `localhost`  
        - `MACHINE_NAME\INSTANCE_NAME`  
     3. Use **double backslashes (`\\`)** in the Python string.  

   - Ensure the following databases exist:  
     - `CustomerDB` → table `Customers`  
     - `AccountDB` → table `Account`
     - `EmailDB` → table `Email`

3. **Run the Services**
   - Customer Service (port 8000):
     ```bash
     uvicorn customer_service:app --reload --port 8000
     ```
   - Account Service (port 8001):
     ```bash
     uvicorn account_service:app --reload --port 8001
     ```
   - Email Service (port 8005):
     ```bash
     uvicorn email_service:app --reload --port 8005
     ```

4. **Access API Documentation**
   - Swagger UI:
     - [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) → Customer Service  
     - [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) → Account Service  
     - [http://127.0.0.1:8005/docs](http://127.0.0.1:8005/docs) → Email Service  


---

## 📂 Project Structure
```
## 📂 Project Structure
Customer_Account_Email/
│
├── account_service.py          # Account service (balance management & notifications)
├── customer_service.py         # Customer service (customer info & tuition debt)
├── email_service.py            # Email service (send emails via Gmail API)
├── send_email.py               # Custom module for Gmail OAuth2 and email sending
│
├── account_serviceDB.sql       # SQL script for AccountDB
├── customer_serviceDB.sql      # SQL script for CustomerDB
├── email_serviceDB.sql         # SQL script for EmailDB
│
├── requirements.txt            # Python dependencies
├── credentials_desktop_apps.json  # Gmail OAuth2 client (keep secret)
└── README.md                   # Project documentation

```
---

## 📝 Notes
- In `BalanceUpdate`, the `description` field is recommended for transaction logging (e.g., "Pay tuition fee").  
  To fully support this, consider creating a `TransactionHistory` table to store all account operations.  
- Always double-check your SQL Server connection string to avoid login errors.  
- Use Swagger UI (`/docs`) for quick testing of APIs in your browser.  
- Run each service on a separate port to prevent conflicts:  
  - Customer → 8000  
  - Account → 8001  
  - Email → 8005  
- `send_email.py` is a custom utility file in this project (not an external dependency).

- Keep `credentials_desktop_apps.json` and `token.json` private.  

---


