# iBanking Application – Tuition Payment Subsystem

The **iBanking Tuition Payment Subsystem** is a backend system built with **FastAPI** and **SQL Server**.  
It provides essential services for managing student tuition payments through an internet banking platform, including authentication, account management, payment processing, OTP verification, and email notification.

---

## 1. System Requirements

- **Python**: 3.11 or later
- **SQL Server Management Studio (SSMS)** – for database setup and management

### Required Python Libraries

- [FastAPI](https://fastapi.tiangolo.com/) – main API framework
- [Uvicorn](https://www.uvicorn.org/) – ASGI server to run FastAPI
- [Pydantic](https://docs.pydantic.dev/) – data validation and request models
- [Requests](https://docs.python-requests.org/) – for service-to-service communication
- [PyODBC](https://github.com/mkleehammer/pyodbc) – SQL Server connector
- [Email-Validator](https://pypi.org/project/email-validator/) – validate email format
- [Passlib](https://passlib.readthedocs.io/en/stable/) – password hashing utilities
- [bcrypt](https://pypi.org/project/bcrypt/) – secure hashing algorithm used by Passlib
- [python-jose](https://pypi.org/project/python-jose/) – JWT encoding and decoding

You can install all dependencies via:

```bash
pip install -r requirements.txt
```

---

## 2. Installation Guide

### Step 1: Create a Virtual Environment

```bash
py -3.11 -m venv venv
```

### Step 2: Activate the Environment

```bash
.\venv\Scripts\activate
```

### Step 3: Configure Database Connections

Each service defines a `get_connection()` function to connect to SQL Server.  
Update the connection string inside these functions according to your environment:

```python
server = "DESKTOP-PV9Q0OQ\SQLEXPRESS"
database = "YourDatabaseName"
```

Replace `DESKTOP-PV9Q0OQ\SQLEXPRESS` with your actual SQL Server instance name.

### Step 4: Initialize Databases

Execute the corresponding `.sql` files in **SSMS** to create databases for each service before running the system.

---

## 3. Project Structure

```
backend/
│
├── authentication_service.py     # Handles login and user verification
├── account_service.py             # Manages account information
├── customer_service.py            # Manages customer details
├── payment_service.py             # Handles tuition payment transactions
├── otp_service.py                 # Generates and verifies OTP codes
├── email_service.py               # Sends OTP and payment confirmation emails
│
├── AuthenticationDB.sql           # Database script for Authentication Service
├── AccountDB.sql                  # Database script for Account Service
├── CustomerDB.sql                 # Database script for Customer Service
├── PaymentDB.sql                  # Database script for Payment Service
├── OTPDB.sql                      # Database script for OTP Service
├── EmailDB.sql                    # Database script for Email Service
│
├── requirements.txt               # Python dependencies
└── README.md                      # Documentation
```

---

## 4. Running the Application

### Step 1: Activate Virtual Environment

```bash
.\venv\Scripts\activate
```

### Step 2: Start Each Service

Run the services separately on different ports as follows:

#### Customer Service (Port 8000)

```bash
python -m uvicorn customer_service:app --reload --port 8000
```

#### Account Service (Port 8001)

```bash
python -m uvicorn account_service:app --reload --port 8001
```

#### Authentication Service (Port 8002)

```bash
python authentication_service.py
```

#### Payment Service (Port 8003)

```bash
python payment_service.py
```

#### OTP Service (Port 8004)

```bash
python otp_service.py
```

#### Email Service (Port 8005)

```bash
python -m uvicorn email_service:app --reload --port 8005
```

---

## 5. API Documentation

Once the services are running, access **Swagger UI** for each module:

| Service Name           | Port | Swagger URL                                              |
| ---------------------- | ---- | -------------------------------------------------------- |
| Customer Service       | 8000 | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| Account Service        | 8001 | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |
| Authentication Service | 8002 | [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs) |
| Payment Service        | 8003 | [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs) |
| OTP Service            | 8004 | [http://127.0.0.1:8004/docs](http://127.0.0.1:8004/docs) |
| Email Service          | 8005 | [http://127.0.0.1:8005/docs](http://127.0.0.1:8005/docs) |

---

## 6. Notes

- All services are designed to operate independently following a **microservices architecture**.
- Communication between services (e.g., Account → Customer) uses **HTTP requests via the `requests` library**.
- Ensure all database scripts are executed before launching the application.
- Each service can be tested individually using its own Swagger UI.
