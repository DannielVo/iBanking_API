from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import pyodbc
from passlib.context import CryptContext

app = FastAPI(title="Authentication Service")

# ================== Logging Config ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ================== Global Exception Handler ==================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unexpected error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error. Please try again later."})

# ================== DB Connection ==================
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=ADIDAPHAT\\MSSQLSERVER01;"
        "DATABASE=AuthenticationDB;"
        "Trusted_Connection=yes;"
    )

# ================== Password Hash ==================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# ================== Models ==================
class LoginRequest(BaseModel):
    username: str
    password: str

class HashRequest(BaseModel):
    password: str

# ================== Endpoints ==================

@app.post("/auth/hash")
def generate_hash(data: HashRequest):
    try:
        hashed = hash_password(data.password)
        logging.info("Password hashed successfully")
        return {"password": data.password, "hash": hashed}
    except Exception as e:
        logging.error(f"Error generating hash: {e}")
        raise HTTPException(status_code=500, detail="Error generating hash")
    
@app.post("/auth/login")
def login(data: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT userId, password_hash FROM authentication WHERE username = ?", (data.username,))
        row = cur.fetchone()
        if not row:
            logging.warning(f"Login failed for non-existent user {data.username}")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        user_id, password_hash = row
        if not verify_password(data.password, password_hash):
            logging.warning(f"Login failed for user {data.username} due to wrong password")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        logging.info(f"User {data.username} logged in successfully")
        return {"message": "Login successful", "userId": user_id}
    finally:
        conn.close()



# ================== Run ==================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
