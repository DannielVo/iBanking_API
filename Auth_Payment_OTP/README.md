# Backend (ChauHuynhThong - 523H0098) - FastAPI

This backend project is built using **FastAPI** and includes the following main services:
- **Authentication Service**
- **Payment Service**
- **OTP Service**

---

## 🚀 System Requirements

To run this project, you need to have the following installed:

- **Python** >= 3.10  
- **Docker** (>= 20.x) — for running Redis  
- **Docker Compose** (>= 2.x)  
- **SQL Server** (>= 2019)  
- **SQL Server Management Studio (SSMS)** to manage the database  
- **Git** (to clone the project)

---

## 🛠️ Installation Guide

### 1. Create and activate a virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```
### 2. Install dependencies

```bash
pip install -r requirements.txt

```

> If you don't have a requirements.txt yet, generate one with: 
```bash
pip freeze > requirements.txt
```


### 3. Configure SQL Server database

The database connection is already defined in database.py:

```
SQLALCHEMY_DATABASE_URL = (
    "mssql+pyodbc://@ADIDAPHAT\\MSSQLSERVER01/FastAPIDB?"
    "driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
```

🔧 Please verify:

Your SQL Server instance (e.g., MSSQLSERVER01) is running

The database FastAPIDB exists:
```bash
CREATE DATABASE FastAPIDB;
```

### 4. Run the FastAPI application

```bash
uvicorn main:app --reload
```
>Then visit http://127.0.0.1:8000/docs
 to interact with the API via Swagger UI.
### 5. Project Structure

```bash
├── main.py              # FastAPI application entry point
├── auth.py              # Authentication logic
├── database.py          # SQL Server connection setup using SQLAlchemy
├── models.py            # ORM model definitions
├── README.md            # This usage guide
├── venv/                # Virtual environment (exclude from commits)
└── __pycache__/         # Python cache files

```

```bash
📌 Notes

- No .env file is required since configuration is directly written in database.py

- Redis is only needed if you use the OTP service (e.g., for temporary OTP storage)

- For production deployment, it is recommended to move configuration to a .env file and use python-dotenv
```

