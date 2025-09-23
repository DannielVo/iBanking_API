# iBanking API – Customer & Account Services

## 📌 Introduction

This project provides a **backend system for iBanking** using **FastAPI**.  
It is divided into two main microservices:

- **Customer Service**: manages customer information and tuition fees.
- **Account Service**: manages accounts, balances, and balance updates (deposit/withdraw).

The system is designed to support online tuition payment workflows.

---

## ⚙️ System Requirements

- **Python**: 3.11+
- **SQL Server** installed and running
- **ODBC Driver**: ODBC Driver 17 for SQL Server

### Required Python Libraries

- [FastAPI](https://fastapi.tiangolo.com/) — main framework for building APIs
- [Uvicorn](https://www.uvicorn.org/) — ASGI server to run FastAPI
- [Pydantic](https://docs.pydantic.dev/) — data validation (BaseModel, EmailStr, Field)
- [Requests](https://docs.python-requests.org/) — HTTP client, used in Account Service to call Customer Service
- [PyODBC](https://github.com/mkleehammer/pyodbc) — SQL Server connector

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
           "DATABASE=AccountDB;"
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

3. **Run the Services**

   - Customer Service (port 8000):
     ```bash
     uvicorn customer_service:app --reload --port 8000
     ```
   - Account Service (port 8001):
     ```bash
     uvicorn account_service:app --reload --port 8001
     ```
   - Authentication Service (port 8002):
     ```bash
     python authentication_service.py
     ```
   - Payment Service (port 8003):

   ```bash
   python payment_service.py
   ```

   - OTP Service (port 8004):

   ```bash
   python OTP_service.py
   ```

4. **Access API Documentation**
   - Swagger UI:
     - [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) → Customer Service
     - [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) → Account Service
     - [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs) → Authentication Service
     - [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs) → Payment Service
     - [http://127.0.0.1:8004/docs](http://127.0.0.1:8004/docs) → OTP Service

---

## 📂 Project Structure

```
Customer_Account_Email/
│
├── account_service.py        # Account service (balance management)
├── customer_service.py       # Customer service (customer info & tuition debt)
├── account_serviceDB.sql     # SQL script for AccountDB
├── customer_serviceDB.sql    # SQL script for CustomerDB
├── requirements.txt          # Dependencies
└── README.md                 # Documentation
```

---

## 📝 Notes

- In `BalanceUpdate`, the `description` field is recommended for transaction logging (e.g., "Pay tuition fee"). To fully support it, consider creating a `TransactionHistory` table.
- Always check your SQL Server connection string carefully to avoid errors.
- Use Swagger UI (`/docs`) for quick testing of APIs.
- Run each service on a separate port to avoid conflicts.

---

## 📊 Usage Examples

### ✅ Get Customer Info

**Request**

```http
GET /customers/101
```

**Response**

```json
{
  "customer_id": "101",
  "full_name": "Nguyen Van A",
  "phone_number": "0909123456",
  "email": "a@example.com",
  "tuition_debt": 500000.0
}
```

### ✅ Get Accounts by Customer

**Request**

```http
GET /account/101
```

**Response**

```json
[
  {
    "customer_id": "101",
    "account_id": "ACC001",
    "balance": 500000.0
  },
  {
    "customer_id": "101",
    "account_id": "ACC002",
    "balance": 2000000.0
  }
]
```

### ✅ Update Balance

**Request**

```http
PUT /account/updateBalance

{
  "account_id": "ACC001",
  "amount": -200000,
  "description": "Pay tuition fee"
}
```

**Response**

```json
{
  "customer_id": "101",
  "account_id": "ACC001",
  "balance": 300000.0,
  "status": "Success"
}
```
